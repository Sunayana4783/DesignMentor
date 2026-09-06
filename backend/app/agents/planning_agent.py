"""
Planning Agent — decides what the student learns next.
Queries the DB for available concepts and asks the LLM to make a pedagogically
sound decision.
"""
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.state import AgentState
from app.agents.prompts import PLANNER_SYSTEM, PLANNER_HUMAN
from app.agents.llm_client import invoke_llm_json
from app.models.progress import UserProgress
from app.models.curriculum import Concept
from app.core.config import settings
from app.core.logging import logger


async def planning_node(state: AgentState, db: AsyncSession) -> dict:
    """
    LangGraph node: picks the next concept for the student.
    Needs DB access — injected as a closure by the orchestrator.
    """
    import uuid
    user_id = uuid.UUID(state["user_id"])
    current_concept = state["concept_slug"]
    mastery_score = state.get("mastery_score", 0.0)
    weak_topics = state.get("weak_subtopics", [])
    evaluation_next_action = state.get("evaluation_next_action", "next_concept")

    # Load all unlocked, not-yet-mastered concepts
    result = await db.execute(
        select(UserProgress, Concept)
        .join(Concept, UserProgress.concept_id == Concept.id)
        .where(
            UserProgress.user_id == user_id,
            UserProgress.is_unlocked == True,
            UserProgress.is_completed == False,
        )
        .order_by(Concept.order_index)
    )
    rows = result.fetchall()

    available_concepts = [
        {
            "slug": concept.slug,
            "name": concept.name,
            "mastery": progress.mastery_score,
            "attempts": progress.attempts,
        }
        for progress, concept in rows
        if concept.slug != current_concept
    ]

    # Load concepts due for review
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    review_result = await db.execute(
        select(UserProgress, Concept)
        .join(Concept, UserProgress.concept_id == Concept.id)
        .where(
            UserProgress.user_id == user_id,
            UserProgress.next_review_date <= now,
        )
    )
    review_rows = review_result.fetchall()
    review_due = [concept.slug for _, concept in review_rows]

    # Determine phase unlocked
    from app.services.progress_service import ProgressService
    dashboard = await ProgressService.get_dashboard(user_id, db)
    phase_unlocked = dashboard.phase_unlocked

    human_prompt = PLANNER_HUMAN.format(
        current_concept=current_concept,
        mastery_score=mastery_score,
        threshold=settings.MASTERY_THRESHOLD,
        weak_topics=", ".join(weak_topics) if weak_topics else "None",
        review_due=", ".join(review_due[:5]) if review_due else "None",
        phase_unlocked=phase_unlocked,
        available_concepts=json.dumps(available_concepts[:10], indent=2),
    )

    logger.info(
        "planning_agent_invoked",
        current=current_concept,
        available=len(available_concepts),
        evaluation_next=evaluation_next_action,
    )

    plan = await invoke_llm_json(PLANNER_SYSTEM, human_prompt, temperature=0.3)

    next_slug = plan.get("next_concept_slug")
    action = plan.get("action", "next_concept")
    reasoning = plan.get("reasoning", "")
    motivation = plan.get("motivation_message", "Great work! Let's keep going.")

    assistant_message = {
        "role": "assistant",
        "content": motivation,
        "agent": "planner",
    }

    return {
        "agent_action": "plan_next",
        "next_concept_slug": next_slug,
        "plan_reasoning": reasoning,
        "messages": [assistant_message],
        "response_message": motivation,
        "response_metadata": {
            "agent": "planner",
            "action": action,
            "next_concept": next_slug,
            "reasoning": reasoning,
        },
    }
