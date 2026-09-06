"""Student memory: mastery tracking, spaced repetition, dashboard aggregation."""
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.progress import UserProgress, MasteryLevel
from app.models.curriculum import Concept, Topic, Phase
from app.models.quiz import QuizAttempt
from app.schemas.learning import DashboardOut, ConceptProgressOut
from app.core.config import settings
from app.core.logging import logger
from app.ml.rf_model import MasteryPredictor
from app.ml.weak_topic_detector import detect_weaknesses


def _score_to_level(score: float) -> MasteryLevel:
    if score < 40:
        return MasteryLevel.BEGINNER
    if score < 60:
        return MasteryLevel.LEARNING
    if score < 75:
        return MasteryLevel.DEVELOPING
    if score < 90:
        return MasteryLevel.GOOD
    return MasteryLevel.MASTERED


def _sm2_next_interval(
    current_interval: int,
    ease_factor: float,
    quality: int,           # 0-5 rating derived from quiz percentage
) -> tuple[int, float]:
    """SM-2 spaced repetition algorithm. Returns (new_interval_days, new_ease_factor)."""
    if quality < 3:
        new_interval = 1
        new_ease = max(settings.SM2_MIN_EASE, ease_factor - 0.2)
    else:
        if current_interval == 1:
            new_interval = 6
        elif current_interval < 6:
            new_interval = round(current_interval * ease_factor)
        else:
            new_interval = round(current_interval * ease_factor)
        new_ease = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ease = max(settings.SM2_MIN_EASE, new_ease)

    return new_interval, new_ease


class ProgressService:

    @staticmethod
    async def get_or_create(
        user_id: uuid.UUID, concept_id: uuid.UUID, db: AsyncSession
    ) -> UserProgress:
        result = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == user_id,
                UserProgress.concept_id == concept_id,
            )
        )
        progress = result.scalar_one_or_none()
        if not progress:
            progress = UserProgress(user_id=user_id, concept_id=concept_id)
            db.add(progress)
            await db.flush()
        return progress

    @staticmethod
    async def update_after_quiz(
        user_id: uuid.UUID,
        attempt: QuizAttempt,
        weak_subtopics: list[str],
        db: AsyncSession,
    ) -> UserProgress:
        progress = await ProgressService.get_or_create(user_id, attempt.concept_id, db)

        now = datetime.now(timezone.utc)
        if not progress.first_attempted_at:
            progress.first_attempted_at = now
        progress.last_attempted_at = now
        progress.attempts += 1

        # Rolling weighted average (recent quiz weights more)
        alpha = 0.4
        progress.mastery_score = (
            alpha * attempt.percentage + (1 - alpha) * progress.mastery_score
            if progress.attempts > 1
            else attempt.percentage
        )
        progress.mastery_level = _score_to_level(progress.mastery_score)
        progress.weak_subtopics = weak_subtopics

        # ── SM-2 update ────────────────────────────────────────────────────
        quality = min(5, int(attempt.percentage / 20))
        new_interval, new_ease = _sm2_next_interval(
            progress.review_interval_days, progress.ease_factor, quality
        )
        progress.review_interval_days = new_interval
        progress.ease_factor = new_ease
        progress.next_review_date = now + timedelta(days=new_interval)

        # ── Build RF feature vector ────────────────────────────────────────
        rf_features = {
            "attempts":               progress.attempts,
            "avg_score":              progress.mastery_score,
            "last_score":             float(attempt.percentage),
            "best_score":             float(attempt.percentage),   # approximation
            "score_trend":            float(attempt.percentage) - progress.mastery_score,
            "score_variance":         0.0,
            "correct_ratio":          (progress.correct_answers / progress.total_answers
                                       if progress.total_answers > 0 else 0.0),
            "total_answers":          progress.total_answers,
            "correct_answers":        progress.correct_answers,
            "weak_topic_count":       len(weak_subtopics),
            "reteach_count":          0,
            "avg_time_per_answer_s":  float(attempt.time_taken_seconds or 0),
            "days_since_first_seen":  0.0,
            "days_since_last_attempt": 0.0,
            "ease_factor":            progress.ease_factor,
            "review_interval_days":   progress.review_interval_days,
            "concept_difficulty":     1,
            "prerequisite_avg_mastery": 75.0,
            "phase":                  1,
            "mode_distribution_quiz": 0.5,
            "consecutive_correct":    0,
        }
        progress.rf_features = rf_features

        # ── RF prediction for mastery ──────────────────────────────────────
        rf_predicted = MasteryPredictor.predict(rf_features)

        # ── Weakness detection blends LLM + RF signals ─────────────────────
        weakness_report = detect_weaknesses(
            concept_slug=str(attempt.concept_id),
            features=rf_features,
            current_mastery=progress.mastery_score,
            eval_weak_topics=weak_subtopics,
        )
        # RF may refine weak subtopic list
        if weakness_report.weak_subtopics:
            progress.weak_subtopics = weakness_report.weak_subtopics

        # Use RF-informed mastery for completion threshold
        effective_mastery = 0.6 * progress.mastery_score + 0.4 * rf_predicted
        if effective_mastery >= settings.MASTERY_THRESHOLD:
            progress.is_completed = True
            if not progress.completed_at:
                progress.completed_at = now

        await db.commit()
        await db.refresh(progress)

        # Unlock next concept if threshold met
        if progress.is_completed:
            await ProgressService._unlock_next_concepts(user_id, attempt.concept_id, db)

        # Trigger background RF retraining check (non-blocking)
        try:
            from app.ml.retraining_service import maybe_retrain
            import asyncio
            asyncio.create_task(maybe_retrain(db))
        except Exception:
            pass  # retraining is best-effort

        logger.info(
            "progress_updated",
            user_id=str(user_id),
            concept_id=str(attempt.concept_id),
            mastery=progress.mastery_score,
        )
        return progress

    @staticmethod
    async def _unlock_next_concepts(
        user_id: uuid.UUID, completed_concept_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Find concepts whose ALL required prerequisites are now completed, unlock them."""
        from app.models.curriculum import ConceptPrerequisite

        # Get all concepts that list this concept as a prerequisite
        result = await db.execute(
            select(ConceptPrerequisite.concept_id).where(
                ConceptPrerequisite.prerequisite_id == completed_concept_id
            )
        )
        dependent_ids = [row[0] for row in result.fetchall()]

        for dep_id in dependent_ids:
            # Check if ALL prerequisites for dep_id are completed
            prereqs = await db.execute(
                select(ConceptPrerequisite.prerequisite_id).where(
                    ConceptPrerequisite.concept_id == dep_id,
                    ConceptPrerequisite.is_required == True,
                )
            )
            prereq_ids = [r[0] for r in prereqs.fetchall()]

            completed_prereqs = await db.execute(
                select(func.count(UserProgress.id)).where(
                    UserProgress.user_id == user_id,
                    UserProgress.concept_id.in_(prereq_ids),
                    UserProgress.is_completed == True,
                )
            )
            completed_count = completed_prereqs.scalar()

            if completed_count == len(prereq_ids):
                dep_progress = await ProgressService.get_or_create(user_id, dep_id, db)
                if not dep_progress.is_unlocked:
                    dep_progress.is_unlocked = True
                    logger.info("concept_unlocked", user_id=str(user_id), concept_id=str(dep_id))

        await db.commit()

    @staticmethod
    async def get_dashboard(user_id: uuid.UUID, db: AsyncSession) -> DashboardOut:
        from app.models.user import User

        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one()

        # All concepts count
        all_concepts_result = await db.execute(
            select(func.count(Concept.id)).where(Concept.is_active == True)
        )
        total_concepts = all_concepts_result.scalar() or 0

        # All progress for this user
        prog_res = await db.execute(
            select(UserProgress, Concept, Topic)
            .join(Concept, UserProgress.concept_id == Concept.id)
            .join(Topic, Concept.topic_id == Topic.id)
            .where(UserProgress.user_id == user_id)
        )
        rows = prog_res.fetchall()

        lld_scores, hld_scores, all_scores = [], [], []
        weak_areas, due_for_review = [], []
        current_concept = None
        mastered_count = 0

        now = datetime.now(timezone.utc)

        for progress, concept, topic in rows:

            all_scores.append(progress.mastery_score)
            if topic.phase == Phase.LLD:
                lld_scores.append(progress.mastery_score)
            elif topic.phase == Phase.HLD:
                hld_scores.append(progress.mastery_score)

            if progress.is_unlocked and not progress.is_completed:
                current_concept = concept.slug

            if progress.weak_subtopics:
                weak_areas.extend(progress.weak_subtopics)

            if (
                progress.next_review_date
                and progress.next_review_date.replace(tzinfo=timezone.utc) <= now
            ):
                due_for_review.append(concept.slug)

            if progress.is_completed:
                mastered_count += 1

        lld_avg = sum(lld_scores) / len(lld_scores) if lld_scores else 0.0
        hld_avg = sum(hld_scores) / len(hld_scores) if hld_scores else 0.0
        overall = sum(all_scores) / len(all_scores) if all_scores else 0.0

        # Determine unlocked phase
        phase_unlocked: str = "foundation"
        if lld_avg >= settings.MASTERY_THRESHOLD:
            phase_unlocked = "hld"
        elif overall > 0:
            phase_unlocked = "lld"

        return DashboardOut(
            user_id=str(user_id),
            username=user.username,
            lld_progress=round(lld_avg, 1),
            hld_progress=round(hld_avg, 1),
            overall_mastery=round(overall, 1),
            current_concept=current_concept,
            weak_areas=list(set(weak_areas))[:5],
            concepts_due_for_review=due_for_review[:5],
            streak_days=0,      # TODO: implement streak tracking
            total_concepts_mastered=mastered_count,
            phase_unlocked=phase_unlocked,
        )

    @staticmethod
    async def get_all_concept_progress(
        user_id: uuid.UUID, db: AsyncSession
    ) -> list[ConceptProgressOut]:
        # Get all concepts
        concepts_result = await db.execute(
            select(Concept).where(Concept.is_active == True).order_by(Concept.order_index)
        )
        all_concepts = concepts_result.scalars().all()

        # Get existing progress records
        progress_result = await db.execute(
            select(UserProgress).where(UserProgress.user_id == user_id)
        )
        progress_map = {p.concept_id: p for p in progress_result.scalars().all()}

        result = []
        for concept in all_concepts:
            progress = progress_map.get(concept.id)
            result.append(ConceptProgressOut(
                concept_slug=concept.slug,
                concept_name=concept.name,
                mastery_score=progress.mastery_score if progress else 0.0,
                mastery_level=progress.mastery_level.value if progress and progress.mastery_level else "not_started",
                attempts=progress.attempts if progress else 0,
                is_unlocked=progress.is_unlocked if progress else (concept.order_index == 1),
                is_completed=progress.is_completed if progress else False,
                next_review_date=progress.next_review_date.isoformat() if progress and progress.next_review_date else None,
                weak_subtopics=progress.weak_subtopics if progress else [],
            ))
        return result
