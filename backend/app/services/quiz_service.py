"""
Quiz Service — manages quiz attempt lifecycle:
  start → submit answers → complete → update progress
"""
import uuid
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.quiz import Question, QuizAttempt, UserAnswer, QuestionType, QuestionDifficulty
from app.models.curriculum import Concept
from app.models.progress import UserProgress
from app.schemas.learning import (
    QuizStartRequest, QuizSessionOut, QuestionOut,
    SubmitAnswerRequest, AnswerFeedback, QuizResultOut,
)
from app.agents.llm_client import invoke_llm_json
from app.agents.prompts import EVALUATOR_SYSTEM, EVALUATOR_HUMAN
from app.services.progress_service import ProgressService
from app.core.config import settings
from app.core.logging import logger
import asyncio


class QuizService:

    # ── Start a quiz session ──────────────────────────────────────────────

    @staticmethod
    async def start_quiz(
        user_id: uuid.UUID,
        req: QuizStartRequest,
        db: AsyncSession,
    ) -> QuizSessionOut:
        # Resolve concept
        concept = await QuizService._get_concept(req.concept_slug, db)

        # Check unlock
        await QuizService._assert_unlocked(user_id, concept.id, db)

        # Fetch or AI-generate questions
        questions = await QuizService._fetch_questions(concept, req.num_questions, db)

        # Create attempt record
        attempt = QuizAttempt(
            id=uuid.uuid4(),
            user_id=user_id,
            concept_id=concept.id,
            max_score=float(sum(q.points for q in questions)),
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)

        q_out = [
            QuestionOut(
                id=q.id,
                question_type=q.question_type.value,
                difficulty=q.difficulty.value,
                content=q.content,
                options=q.question_metadata.get("options") if q.question_type == QuestionType.MCQ else None,
                points=q.points,
            )
            for q in questions
        ]

        return QuizSessionOut(
            attempt_id=attempt.id,
            concept_slug=req.concept_slug,
            questions=q_out,
        )

    # ── Submit a single answer ────────────────────────────────────────────

    @staticmethod
    async def submit_answer(
        user_id: uuid.UUID,
        req: SubmitAnswerRequest,
        db: AsyncSession,
    ) -> AnswerFeedback:
        attempt = await QuizService._get_attempt(req.attempt_id, user_id, db)
        question = await QuizService._get_question(req.question_id, db)

        # Evaluate answer with AI
        feedback = await QuizService._evaluate_answer(question, req.user_response, db)

        # Persist answer
        answer = UserAnswer(
            id=uuid.uuid4(),
            attempt_id=attempt.id,
            question_id=question.id,
            user_response=req.user_response,
            is_correct=feedback["is_correct"],
            score_awarded=float(feedback["score_awarded"]),
            ai_evaluation=feedback["feedback"],
            evaluation_details=feedback,
        )
        db.add(answer)
        await db.commit()

        return AnswerFeedback(
            question_id=question.id,
            is_correct=feedback["is_correct"],
            score_awarded=feedback["score_awarded"],
            ai_evaluation=feedback["feedback"],
            correct_explanation=feedback.get("explanation", ""),
        )

    # ── Complete a quiz attempt ───────────────────────────────────────────

    @staticmethod
    async def complete_quiz(
        user_id: uuid.UUID,
        attempt_id: uuid.UUID,
        db: AsyncSession,
    ) -> QuizResultOut:
        attempt = await QuizService._get_attempt(attempt_id, user_id, db)

        # Aggregate scores from answers
        answers_result = await db.execute(
            select(UserAnswer).where(UserAnswer.attempt_id == attempt.id)
        )
        answers = answers_result.scalars().all()

        total_score = sum(a.score_awarded for a in answers)
        percentage = (total_score / attempt.max_score * 100) if attempt.max_score > 0 else 0.0
        passed = percentage >= settings.MASTERY_THRESHOLD

        # Identify weak subtopics from wrong answers
        wrong_answers = [a for a in answers if not a.is_correct]
        weak_subtopics = []
        for a in wrong_answers:
            topics = a.evaluation_details.get("weak_subtopics", [])
            weak_subtopics.extend(topics)
        weak_subtopics = list(set(weak_subtopics))[:5]

        # Build overall AI feedback
        ai_feedback = await QuizService._generate_quiz_summary(
            answers, percentage, weak_subtopics
        )

        # Close attempt
        now = datetime.now(timezone.utc)
        attempt.score = total_score
        attempt.percentage = percentage
        attempt.passed = passed
        attempt.ai_feedback = ai_feedback
        attempt.weak_subtopics = weak_subtopics
        attempt.completed_at = now
        if answers:
            # estimate time from first to last answer
            first = min(a.answered_at for a in answers)
            if first.tzinfo is None:
                first = first.replace(tzinfo=timezone.utc)
            attempt.time_taken_seconds = int((now - first).total_seconds())
        await db.commit()
        await db.refresh(attempt)

        # Update progress
        progress = await ProgressService.update_after_quiz(
            user_id=user_id,
            attempt=attempt,
            weak_subtopics=weak_subtopics,
            db=db,
        )

        # Determine next concept
        next_concept = None
        if passed and progress.is_completed:
            next_res = await db.execute(
                select(Concept)
                .join(UserProgress, Concept.id == UserProgress.concept_id)
                .where(
                    UserProgress.user_id == user_id,
                    UserProgress.is_unlocked == True,
                    UserProgress.is_completed == False,
                )
                .order_by(Concept.order_index)
                .limit(1)
            )
            nc = next_res.scalar_one_or_none()
            if nc:
                next_concept = nc.slug

        next_action = (
            "next_concept" if passed
            else ("reteach" if percentage < 50 else "practice_more")
        )

        concept_res = await db.execute(
            select(Concept).where(Concept.id == attempt.concept_id)
        )
        concept = concept_res.scalar_one()

        return QuizResultOut(
            attempt_id=attempt.id,
            concept_slug=concept.slug,
            score=total_score,
            max_score=attempt.max_score,
            percentage=round(percentage, 1),
            passed=passed,
            mastery_level=progress.mastery_level.value,
            ai_feedback=ai_feedback,
            weak_subtopics=weak_subtopics,
            next_action=next_action,
            next_concept_slug=next_concept,
        )

    # ── Private helpers ───────────────────────────────────────────────────

    @staticmethod
    async def _get_concept(slug: str, db: AsyncSession) -> Concept:
        result = await db.execute(select(Concept).where(Concept.slug == slug, Concept.is_active == True))
        concept = result.scalar_one_or_none()
        if not concept:
            raise HTTPException(status_code=404, detail=f"Concept '{slug}' not found")
        return concept

    @staticmethod
    async def _get_attempt(attempt_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> QuizAttempt:
        result = await db.execute(
            select(QuizAttempt).where(QuizAttempt.id == attempt_id, QuizAttempt.user_id == user_id)
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=404, detail="Quiz attempt not found")
        return attempt

    @staticmethod
    async def _get_question(question_id: uuid.UUID, db: AsyncSession) -> Question:
        result = await db.execute(select(Question).where(Question.id == question_id))
        q = result.scalar_one_or_none()
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        return q

    @staticmethod
    async def _assert_unlocked(user_id: uuid.UUID, concept_id: uuid.UUID, db: AsyncSession) -> None:
        result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.concept_id == concept_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            # Auto-create and unlock progress record on first quiz attempt
            progress = UserProgress(
                user_id=user_id,
                concept_id=concept_id,
                is_unlocked=True,
            )
            db.add(progress)
            await db.flush()
        elif not progress.is_unlocked:
            # Auto-unlock — don't block the student
            progress.is_unlocked = True
            await db.flush()

    @staticmethod
    async def _fetch_questions(
        concept: Concept, num: int, db: AsyncSession
    ) -> list[Question]:
        """Fetch existing DB questions; AI-generate if insufficient."""
        result = await db.execute(
            select(Question)
            .where(Question.concept_id == concept.id, Question.is_active == True)
            .order_by(Question.difficulty)
        )
        all_questions = result.scalars().all()

        if len(all_questions) >= num:
            # Shuffle to avoid same order every time
            import random
            questions = list(all_questions)
            random.shuffle(questions)
            return questions[:num]

        # AI-generate the remaining questions and persist them
        needed = num - len(all_questions)
        ai_questions = await QuizService._ai_generate_questions(concept, needed)
        new_questions = []
        for q_data in ai_questions:
            q = Question(
                id=uuid.uuid4(),
                concept_id=concept.id,
                question_type=QuestionType(q_data.get("question_type", "short_answer")),
                difficulty=QuestionDifficulty(q_data.get("difficulty", "medium")),
                content=q_data["content"],
                question_metadata={
                    "options": q_data.get("options", []),
                    "correct_answer": q_data.get("correct_answer", ""),
                    "expected_answer_points": q_data.get("expected_answer_points", []),
                },
                points=int(q_data.get("points", 10)),
            )
            db.add(q)
            new_questions.append(q)
        await db.commit()

        import random
        all_q = list(all_questions) + new_questions
        random.shuffle(all_q)
        return all_q[:num]

    @staticmethod
    async def _ai_generate_questions(concept: Concept, count: int) -> list[dict]:
        """Use Quiz Agent prompt to generate questions on-the-fly."""
        from app.agents.prompts import QUIZ_SYSTEM, QUIZ_HUMAN
        easy = max(1, count // 3)
        medium = max(1, count // 2)
        hard = count - easy - medium
        human = QUIZ_HUMAN.format(
            concept_name=concept.name,
            num_questions=count,
            easy_count=easy,
            medium_count=medium,
            hard_count=hard,
            weak_subtopics="Cover all sub-topics evenly",
            previous_questions="[]",
        )
        try:
            result = await invoke_llm_json(QUIZ_SYSTEM, human, temperature=0.7)
            if isinstance(result, dict):
                return result.get("questions", [result])
            return result if isinstance(result, list) else []
        except Exception:
            # Fallback questions — mix of theory, MCQ, code, scenario
            import random
            fallbacks = [
                # Theory
                {
                    "question_type": "short_answer",
                    "difficulty": "easy",
                    "content": f"In one sentence, what is {concept.name} and why does it exist?",
                    "expected_answer_points": [concept.description],
                    "points": 10,
                },
                # MCQ
                {
                    "question_type": "mcq",
                    "difficulty": "easy",
                    "content": f"Which of the following BEST describes {concept.name}?",
                    "options": [
                        f"A) {concept.description[:80]}",
                        "B) A way to make code run faster at runtime",
                        "C) A database design technique",
                        "D) A networking protocol",
                    ],
                    "correct_answer": "A",
                    "expected_answer_points": [],
                    "points": 10,
                },
                # Code/Problem
                {
                    "question_type": "debugging",
                    "difficulty": "medium",
                    "content": f"A developer says: 'I understand {concept.name} in theory, but I'm not sure when to actually USE it in a real project.' Give them 2 concrete real-world scenarios where applying {concept.name} would make the code significantly better.",
                    "expected_answer_points": ["scenario 1", "scenario 2", "why it helps"],
                    "points": 10,
                },
                # Scenario
                {
                    "question_type": "scenario",
                    "difficulty": "medium",
                    "content": f"Your team is building an e-commerce platform. A senior engineer suggests using {concept.name} for the payment module. Another engineer disagrees and says it adds unnecessary complexity. Who is right, and why? What questions would you ask to decide?",
                    "expected_answer_points": ["trade-offs", "when to apply", "context matters"],
                    "points": 10,
                },
                # Code writing
                {
                    "question_type": "design",
                    "difficulty": "hard",
                    "content": f"Write a minimal code example (10-15 lines, any language) that demonstrates {concept.name} correctly. Then write a SECOND version that violates it, and explain the difference.",
                    "expected_answer_points": ["correct example", "violation example", "explanation of difference"],
                    "points": 10,
                },
                # MCQ — harder
                {
                    "question_type": "mcq",
                    "difficulty": "hard",
                    "content": f"Which statement about {concept.name} is FALSE?",
                    "options": [
                        "A) It can improve code maintainability",
                        "B) It always makes code run faster",
                        "C) It is a widely used principle in object-oriented design",
                        "D) It can make code easier to test",
                    ],
                    "correct_answer": "B",
                    "expected_answer_points": [],
                    "points": 10,
                },
                # Interview style
                {
                    "question_type": "scenario",
                    "difficulty": "hard",
                    "content": f"In a system design interview, you are asked: 'How does {concept.name} help when building a large-scale application with 50 developers?' Give a structured answer covering: (1) the problem it solves at scale, (2) a concrete example, (3) potential downsides.",
                    "expected_answer_points": ["problem at scale", "example", "downsides"],
                    "points": 10,
                },
            ]
            random.shuffle(fallbacks)
            return fallbacks[:count]

    @staticmethod
    async def _evaluate_answer(question: Question, user_response: str, db: AsyncSession) -> dict:
        """Evaluate a single answer using the Evaluation Agent prompt."""
        expected = question.question_metadata.get("expected_answer_points", [])
        correct_answer = question.question_metadata.get("correct_answer", "")

        # MCQ: check directly
        if question.question_type == QuestionType.MCQ:
            is_correct = (
                user_response.strip().upper().startswith(correct_answer.upper())
                if correct_answer else False
            )
            return {
                "is_correct": is_correct,
                "score_awarded": float(question.points) if is_correct else 0.0,
                "feedback": "Correct!" if is_correct else f"The correct answer was {correct_answer}.",
                "explanation": question.question_metadata.get("explanation", ""),
                "weak_subtopics": [] if is_correct else ["recall"],
            }

        # Open-ended: use LLM evaluator
        human = EVALUATOR_HUMAN.format(
            concept_name="Quiz Question",
            threshold=settings.MASTERY_THRESHOLD,
            question=question.content,
            question_type=question.question_type.value,
            user_answer=user_response,
            expected_points=json.dumps(expected),
            current_mastery=50,
            weak_subtopics="",
            reteach_count=0,
        )
        try:
            result = await invoke_llm_json(EVALUATOR_SYSTEM, human, temperature=0.2)
            score_pct = float(result.get("score", 50)) / 100
            return {
                "is_correct": score_pct >= 0.6,
                "score_awarded": score_pct * question.points,
                "feedback": result.get("feedback", "Answer recorded."),
                "explanation": "",
                "weak_subtopics": result.get("weak_subtopics", []),
            }
        except Exception as exc:
            logger.warning("answer_eval_failed", error=str(exc))
            # Give partial credit on evaluation failure
            return {
                "is_correct": True,
                "score_awarded": float(question.points) * 0.5,
                "feedback": "Your answer was recorded. AI evaluation temporarily unavailable.",
                "weak_subtopics": [],
            }

    @staticmethod
    async def _generate_quiz_summary(
        answers: list[UserAnswer], percentage: float, weak_subtopics: list[str]
    ) -> str:
        correct = sum(1 for a in answers if a.is_correct)
        total = len(answers)
        summary_parts = [
            f"You got {correct}/{total} questions correct ({percentage:.1f}%).",
        ]
        if weak_subtopics:
            summary_parts.append(f"Areas to focus on: {', '.join(weak_subtopics)}.")
        if percentage >= 90:
            summary_parts.append("Excellent work! You've mastered this concept.")
        elif percentage >= 75:
            summary_parts.append("Good job! You're developing a solid understanding.")
        elif percentage >= 50:
            summary_parts.append("You're making progress. A bit more practice will cement this.")
        else:
            summary_parts.append("Let's go over this concept again with a focus on the weak areas.")
        return " ".join(summary_parts)
