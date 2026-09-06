"""
Retraining Service — collects real student data from the DB and triggers
Random Forest retraining when enough samples have accumulated.

Design:
  - Runs as a background task triggered after every quiz completion
  - Uses a counter stored in Redis to avoid retraining too frequently
  - Builds feature vectors from UserProgress + QuizAttempt history
  - Calls MasteryPredictor.retrain() with the accumulated dataset
"""
import uuid
import numpy as np
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.rf_model import MasteryPredictor, score_to_label
from app.ml.features import (
    MasteryFeatures,
    build_features_from_progress,
    DIFFICULTY_MAP,
    PHASE_MAP,
)
from app.models.progress import UserProgress
from app.models.curriculum import Concept, Topic
from app.models.quiz import QuizAttempt
from app.core.config import settings
from app.core.cache import cache_get, cache_set
from app.core.logging import logger

_RETRAIN_COUNTER_KEY = "rf:retrain_counter"
_RETRAIN_LOCK_KEY    = "rf:retrain_lock"


async def maybe_retrain(db: AsyncSession) -> bool:
    """
    Called after every quiz completion.
    Increments a counter in Redis; triggers retraining every N completions.
    Returns True if retraining was triggered.
    """
    # Check lock to avoid concurrent retraining
    lock = await cache_get(_RETRAIN_LOCK_KEY)
    if lock:
        return False

    counter = (await cache_get(_RETRAIN_COUNTER_KEY)) or 0
    counter = int(counter) + 1
    await cache_set(_RETRAIN_COUNTER_KEY, counter, ttl=86400 * 7)

    if counter % settings.RF_RETRAIN_EVERY_N_ATTEMPTS != 0:
        return False

    logger.info("rf_retraining_triggered", attempt_count=counter)
    await cache_set(_RETRAIN_LOCK_KEY, "1", ttl=300)  # 5-min lock

    try:
        X, y = await _collect_training_data(db)
        if len(X) < 50:
            logger.info("rf_retrain_skipped_insufficient_data", samples=len(X))
            return False

        result = MasteryPredictor.retrain(X, y)
        logger.info("rf_retrain_complete", **result)
        return True
    except Exception as exc:
        logger.error("rf_retrain_failed", error=str(exc))
        return False
    finally:
        await cache_set(_RETRAIN_LOCK_KEY, "", ttl=1)


async def _collect_training_data(
    db: AsyncSession,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Collect feature vectors and mastery labels from the database.
    Each row = one (user, concept) pair with aggregated quiz history.
    """
    # Load all progress records that have been attempted at least once
    result = await db.execute(
        select(UserProgress, Concept, Topic)
        .join(Concept, UserProgress.concept_id == Concept.id)
        .join(Topic,   Concept.topic_id == Topic.id)
        .where(UserProgress.attempts > 0)
    )
    rows = result.fetchall()

    X_rows: list[np.ndarray] = []
    y_rows: list[float]      = []

    for progress, concept, topic in rows:
        # Fetch quiz scores and times for this (user, concept) pair
        attempts_result = await db.execute(
            select(QuizAttempt.percentage, QuizAttempt.time_taken_seconds)
            .where(
                QuizAttempt.user_id == progress.user_id,
                QuizAttempt.concept_id == progress.concept_id,
            )
            .order_by(QuizAttempt.started_at)
        )
        attempt_rows = attempts_result.fetchall()
        quiz_scores = [float(r.percentage) for r in attempt_rows]
        quiz_times  = [int(r.time_taken_seconds or 0) for r in attempt_rows]

        if not quiz_scores:
            continue

        # Days since first/last attempt
        now = datetime.now(timezone.utc)
        days_first = 0.0
        days_last  = 0.0
        if progress.first_attempted_at:
            fa = progress.first_attempted_at
            if fa.tzinfo is None:
                fa = fa.replace(tzinfo=timezone.utc)
            days_first = (now - fa).days
        if progress.last_attempted_at:
            la = progress.last_attempted_at
            if la.tzinfo is None:
                la = la.replace(tzinfo=timezone.utc)
            days_last = (now - la).days

        # Average mastery of prerequisites
        prereq_mastery = await _avg_prereq_mastery(
            progress.user_id, concept.id, db
        )

        progress_dict = {
            "total_answers":     progress.total_answers,
            "correct_answers":   progress.correct_answers,
            "weak_subtopics":    progress.weak_subtopics or [],
            "reteach_count":     0,
            "ease_factor":       progress.ease_factor,
            "review_interval_days": progress.review_interval_days,
        }

        feat = build_features_from_progress(
            progress_data=progress_dict,
            quiz_scores=quiz_scores,
            quiz_times=quiz_times,
            concept_difficulty=concept.difficulty.value,
            phase=topic.phase.value,
            prerequisite_avg_mastery=prereq_mastery,
            days_since_first_seen=days_first,
            days_since_last_attempt=days_last,
        )

        X_rows.append(feat.to_array())
        y_rows.append(float(progress.mastery_score))

    if not X_rows:
        return np.empty((0, len(MasteryFeatures.column_names()))), np.empty(0)

    return np.vstack(X_rows).astype(np.float32), np.array(y_rows, dtype=np.float32)


async def _avg_prereq_mastery(
    user_id: uuid.UUID,
    concept_id: uuid.UUID,
    db: AsyncSession,
) -> float:
    """Average mastery score across all required prerequisites."""
    from app.models.curriculum import ConceptPrerequisite

    prereq_ids_result = await db.execute(
        select(ConceptPrerequisite.prerequisite_id).where(
            ConceptPrerequisite.concept_id == concept_id,
            ConceptPrerequisite.is_required == True,
        )
    )
    prereq_ids = [r[0] for r in prereq_ids_result.fetchall()]

    if not prereq_ids:
        return 100.0  # no prerequisites = full mastery credit

    mastery_result = await db.execute(
        select(func.avg(UserProgress.mastery_score)).where(
            UserProgress.user_id == user_id,
            UserProgress.concept_id.in_(prereq_ids),
        )
    )
    avg = mastery_result.scalar()
    return float(avg) if avg is not None else 0.0


async def build_features_for_user_concept(
    user_id: uuid.UUID,
    concept_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """
    Build a feature dict for a specific (user, concept) pair.
    Called by the progress service to update rf_features in UserProgress.
    """
    progress_result = await db.execute(
        select(UserProgress, Concept, Topic)
        .join(Concept, UserProgress.concept_id == Concept.id)
        .join(Topic, Concept.topic_id == Topic.id)
        .where(
            UserProgress.user_id == user_id,
            UserProgress.concept_id == concept_id,
        )
    )
    row = progress_result.one_or_none()
    if not row:
        return {}

    progress, concept, topic = row

    attempts_result = await db.execute(
        select(QuizAttempt.percentage, QuizAttempt.time_taken_seconds)
        .where(
            QuizAttempt.user_id == user_id,
            QuizAttempt.concept_id == concept_id,
        )
        .order_by(QuizAttempt.started_at)
    )
    attempt_rows = attempts_result.fetchall()
    quiz_scores = [float(r.percentage) for r in attempt_rows]
    quiz_times  = [int(r.time_taken_seconds or 0) for r in attempt_rows]

    now = datetime.now(timezone.utc)
    days_first = 0.0
    days_last  = 0.0
    if progress.first_attempted_at:
        fa = progress.first_attempted_at
        if fa.tzinfo is None:
            fa = fa.replace(tzinfo=timezone.utc)
        days_first = (now - fa).days
    if progress.last_attempted_at:
        la = progress.last_attempted_at
        if la.tzinfo is None:
            la = la.replace(tzinfo=timezone.utc)
        days_last = (now - la).days

    prereq_mastery = await _avg_prereq_mastery(user_id, concept_id, db)

    progress_dict = {
        "total_answers":     progress.total_answers,
        "correct_answers":   progress.correct_answers,
        "weak_subtopics":    progress.weak_subtopics or [],
        "reteach_count":     0,
        "ease_factor":       progress.ease_factor,
        "review_interval_days": progress.review_interval_days,
    }

    feat = build_features_from_progress(
        progress_data=progress_dict,
        quiz_scores=quiz_scores,
        quiz_times=quiz_times,
        concept_difficulty=concept.difficulty.value,
        phase=topic.phase.value,
        prerequisite_avg_mastery=prereq_mastery,
        days_since_first_seen=days_first,
        days_since_last_attempt=days_last,
    )

    from dataclasses import asdict
    return asdict(feat)
