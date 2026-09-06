"""
Feature engineering for the Random Forest mastery predictor.

Features derived from UserProgress + QuizAttempt history.
All features are numeric so sklearn can consume them directly.
"""
from dataclasses import dataclass, asdict
from typing import Optional
import numpy as np


@dataclass
class MasteryFeatures:
    # ── Quiz performance ───────────────────────────────────────────────────
    attempts:               int     = 0     # total quiz attempts for this concept
    avg_score:              float   = 0.0   # rolling average quiz percentage
    last_score:             float   = 0.0   # most recent quiz percentage
    best_score:             float   = 0.0   # best quiz percentage ever
    score_trend:            float   = 0.0   # last_score - avg_score (positive = improving)
    score_variance:         float   = 0.0   # variance across attempts

    # ── Answer quality ─────────────────────────────────────────────────────
    correct_ratio:          float   = 0.0   # correct_answers / total_answers
    total_answers:          int     = 0
    correct_answers:        int     = 0

    # ── Weak topic signals ─────────────────────────────────────────────────
    weak_topic_count:       int     = 0     # number of identified weak sub-topics
    reteach_count:          int     = 0     # how many times the concept was retaught

    # ── Time signals ──────────────────────────────────────────────────────
    avg_time_per_answer_s:  float   = 0.0   # faster answers often indicate recall vs learning
    days_since_first_seen:  float   = 0.0
    days_since_last_attempt: float  = 0.0

    # ── Spaced repetition signals ─────────────────────────────────────────
    ease_factor:            float   = 2.5   # SM-2 ease factor
    review_interval_days:   int     = 1

    # ── Curriculum position signals ────────────────────────────────────────
    concept_difficulty:     int     = 1     # 0=beginner, 1=intermediate, 2=advanced, 3=expert
    prerequisite_avg_mastery: float = 0.0  # average mastery of prerequisite concepts
    phase:                  int     = 0     # 0=foundation, 1=lld, 2=hld

    # ── Session behaviour ─────────────────────────────────────────────────
    mode_distribution_quiz: float   = 0.0  # fraction of sessions in quiz mode
    consecutive_correct:    int     = 0    # streak of correct answers

    def to_array(self) -> np.ndarray:
        """Return features as a 1D numpy array in a stable column order."""
        return np.array(list(asdict(self).values()), dtype=np.float32)

    @classmethod
    def column_names(cls) -> list[str]:
        return list(cls.__dataclass_fields__.keys())

    @classmethod
    def from_dict(cls, d: dict) -> "MasteryFeatures":
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**filtered)


DIFFICULTY_MAP = {
    "beginner":     0,
    "intermediate": 1,
    "advanced":     2,
    "expert":       3,
}

PHASE_MAP = {
    "foundation": 0,
    "lld":        1,
    "hld":        2,
}


def build_features_from_progress(
    progress_data: dict,
    quiz_scores: list[float],
    quiz_times: list[int],
    concept_difficulty: str = "intermediate",
    phase: str = "lld",
    prerequisite_avg_mastery: float = 0.0,
    days_since_first_seen: float = 0.0,
    days_since_last_attempt: float = 0.0,
) -> MasteryFeatures:
    """
    Build a MasteryFeatures object from raw progress data.
    Called when updating progress after a quiz attempt.
    """
    attempts = len(quiz_scores)
    avg_score = float(np.mean(quiz_scores)) if quiz_scores else 0.0
    last_score = quiz_scores[-1] if quiz_scores else 0.0
    best_score = float(np.max(quiz_scores)) if quiz_scores else 0.0
    score_trend = last_score - avg_score
    score_variance = float(np.var(quiz_scores)) if len(quiz_scores) > 1 else 0.0

    total_answers = progress_data.get("total_answers", 0)
    correct_answers = progress_data.get("correct_answers", 0)
    correct_ratio = correct_answers / total_answers if total_answers > 0 else 0.0

    avg_time = float(np.mean(quiz_times)) if quiz_times else 0.0

    return MasteryFeatures(
        attempts=attempts,
        avg_score=avg_score,
        last_score=last_score,
        best_score=best_score,
        score_trend=score_trend,
        score_variance=score_variance,
        correct_ratio=correct_ratio,
        total_answers=total_answers,
        correct_answers=correct_answers,
        weak_topic_count=len(progress_data.get("weak_subtopics", [])),
        reteach_count=progress_data.get("reteach_count", 0),
        avg_time_per_answer_s=avg_time,
        days_since_first_seen=days_since_first_seen,
        days_since_last_attempt=days_since_last_attempt,
        ease_factor=progress_data.get("ease_factor", 2.5),
        review_interval_days=progress_data.get("review_interval_days", 1),
        concept_difficulty=DIFFICULTY_MAP.get(concept_difficulty, 1),
        prerequisite_avg_mastery=prerequisite_avg_mastery,
        phase=PHASE_MAP.get(phase, 1),
        mode_distribution_quiz=progress_data.get("mode_distribution_quiz", 0.0),
        consecutive_correct=progress_data.get("consecutive_correct", 0),
    )
