"""
Weak Topic Detector — analyses quiz answer patterns to identify
specific sub-topics the student struggles with.

Uses a combination of:
  1. RF feature importance — which features explain low mastery
  2. Answer pattern analysis — repeated wrong answers on specific sub-topics
  3. Concept graph traversal — if prerequisite X is weak, flag downstream
"""
from dataclasses import dataclass
from app.ml.rf_model import MasteryPredictor
from app.core.logging import logger


@dataclass
class WeaknessReport:
    concept_slug:       str
    overall_mastery:    float
    predicted_mastery:  float
    confidence:         float           # RF confidence (1 - std of tree predictions)
    weak_subtopics:     list[str]
    priority_action:    str             # "reteach" | "practice_more" | "next_concept"
    explanation:        str


# Sub-topic keywords per concept category
# The RF model flags features; we map them back to concept vocabulary
FEATURE_TO_SUBTOPIC: dict[str, list[str]] = {
    "correct_ratio":         ["basic recall", "fundamental understanding"],
    "score_variance":        ["consistency", "reliability of knowledge"],
    "weak_topic_count":      ["specific sub-topics"],
    "reteach_count":         ["foundational understanding"],
    "avg_time_per_answer_s": ["fluency", "recall speed"],
    "score_trend":           ["retention", "progressive learning"],
    "prerequisite_avg_mastery": ["prerequisite knowledge gaps"],
    "ease_factor":           ["learning velocity"],
}


def detect_weaknesses(
    concept_slug: str,
    features: dict,
    current_mastery: float,
    threshold: float = 75.0,
    eval_weak_topics: list[str] | None = None,
) -> WeaknessReport:
    """
    Combine RF signals with evaluation agent output to produce a
    structured weakness report.
    """
    predicted = MasteryPredictor.predict(features)
    proba = MasteryPredictor.predict_proba(features)

    # Confidence = max probability of top-2 classes
    sorted_proba = sorted(proba.values(), reverse=True)
    confidence = sum(sorted_proba[:2]) if len(sorted_proba) >= 2 else max(sorted_proba, default=0.5)

    # Identify which features are pulling mastery down
    importances = MasteryPredictor.feature_importances()
    weak_signals: list[str] = []

    if features:
        # Features that are "bad" and highly important
        bad_feature_checks = {
            "correct_ratio":         lambda v: float(v) < 0.6,
            "score_variance":        lambda v: float(v) > 300,
            "weak_topic_count":      lambda v: float(v) >= 2,
            "reteach_count":         lambda v: float(v) >= 2,
            "score_trend":           lambda v: float(v) < -10,
            "avg_time_per_answer_s": lambda v: float(v) > 90,
            "prerequisite_avg_mastery": lambda v: float(v) < 60,
        }
        for feat_name, is_bad in bad_feature_checks.items():
            val = features.get(feat_name)
            if val is not None and is_bad(val):
                importance = importances.get(feat_name, 0)
                if importance > 0.02:  # only flag high-importance features
                    weak_signals.extend(FEATURE_TO_SUBTOPIC.get(feat_name, [feat_name]))

    # Merge with evaluation agent's identified weak topics
    all_weak = list(set(weak_signals + (eval_weak_topics or [])))

    # Determine priority action
    if predicted < threshold * 0.6:
        action = "reteach"
        explanation = (
            f"RF model predicts mastery at {predicted:.1f}% — well below the "
            f"{threshold}% threshold. Focus on: {', '.join(all_weak[:3]) or 'foundational understanding'}."
        )
    elif predicted < threshold:
        action = "practice_more"
        explanation = (
            f"RF predicts {predicted:.1f}% mastery — close to the {threshold}% threshold. "
            f"A few more practice questions on {', '.join(all_weak[:2]) or 'key concepts'} will solidify understanding."
        )
    else:
        action = "next_concept"
        explanation = (
            f"RF predicts {predicted:.1f}% mastery — above the {threshold}% threshold. "
            "Ready to progress to the next concept."
        )

    logger.info(
        "weakness_detected",
        concept=concept_slug,
        current=current_mastery,
        predicted=predicted,
        action=action,
        weak_count=len(all_weak),
    )

    return WeaknessReport(
        concept_slug=concept_slug,
        overall_mastery=current_mastery,
        predicted_mastery=predicted,
        confidence=round(confidence, 3),
        weak_subtopics=all_weak[:5],
        priority_action=action,
        explanation=explanation,
    )
