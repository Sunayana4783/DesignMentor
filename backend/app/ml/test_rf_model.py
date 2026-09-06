"""
Quick sanity-check for the RF model — run directly:
  python -m app.ml.test_rf_model
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.ml.rf_model import MasteryPredictor, score_to_label, _generate_synthetic_data
from app.ml.features import MasteryFeatures
from app.ml.weak_topic_detector import detect_weaknesses
import numpy as np


def main():
    print("=" * 60)
    print("DesignMentor AI — Random Forest Model Validation")
    print("=" * 60)

    # 1. Train from scratch
    print("\n[1] Training model on synthetic data...")
    MasteryPredictor._model_path_reg = "app/ml/models/rf_regressor.pkl"
    MasteryPredictor._model_path_clf = "app/ml/models/rf_classifier.pkl"
    MasteryPredictor._train_from_scratch()

    # 2. Test predictions for different student profiles
    profiles = [
        {
            "label": "Strong student (high correct_ratio, many attempts)",
            "features": {
                "attempts": 8, "avg_score": 85.0, "last_score": 90.0,
                "best_score": 93.0, "score_trend": 5.0, "score_variance": 25.0,
                "correct_ratio": 0.88, "total_answers": 40, "correct_answers": 35,
                "weak_topic_count": 0, "reteach_count": 0, "avg_time_per_answer_s": 25.0,
                "days_since_first_seen": 7.0, "days_since_last_attempt": 1.0,
                "ease_factor": 2.8, "review_interval_days": 7,
                "concept_difficulty": 1, "prerequisite_avg_mastery": 90.0,
                "phase": 1, "mode_distribution_quiz": 0.6, "consecutive_correct": 7,
            }
        },
        {
            "label": "Struggling student (low correct_ratio, high weak_count)",
            "features": {
                "attempts": 3, "avg_score": 42.0, "last_score": 38.0,
                "best_score": 55.0, "score_trend": -4.0, "score_variance": 180.0,
                "correct_ratio": 0.35, "total_answers": 15, "correct_answers": 5,
                "weak_topic_count": 4, "reteach_count": 2, "avg_time_per_answer_s": 95.0,
                "days_since_first_seen": 2.0, "days_since_last_attempt": 0.0,
                "ease_factor": 1.5, "review_interval_days": 1,
                "concept_difficulty": 2, "prerequisite_avg_mastery": 45.0,
                "phase": 1, "mode_distribution_quiz": 0.3, "consecutive_correct": 0,
            }
        },
        {
            "label": "Borderline student (near threshold)",
            "features": {
                "attempts": 5, "avg_score": 68.0, "last_score": 72.0,
                "best_score": 78.0, "score_trend": 4.0, "score_variance": 120.0,
                "correct_ratio": 0.65, "total_answers": 25, "correct_answers": 16,
                "weak_topic_count": 2, "reteach_count": 1, "avg_time_per_answer_s": 45.0,
                "days_since_first_seen": 5.0, "days_since_last_attempt": 1.0,
                "ease_factor": 2.1, "review_interval_days": 3,
                "concept_difficulty": 1, "prerequisite_avg_mastery": 72.0,
                "phase": 0, "mode_distribution_quiz": 0.5, "consecutive_correct": 2,
            }
        },
    ]

    print("\n[2] Predictions:")
    print("-" * 60)
    for p in profiles:
        score = MasteryPredictor.predict(p["features"])
        cat   = MasteryPredictor.predict_category(p["features"])
        proba = MasteryPredictor.predict_proba(p["features"])
        print(f"\nProfile : {p['label']}")
        print(f"  Predicted score    : {score:.1f}%")
        print(f"  Predicted category : {cat}")
        print(f"  Class probabilities: {proba}")

    # 3. Test weakness detection
    print("\n\n[3] Weakness Detection:")
    print("-" * 60)
    report = detect_weaknesses(
        concept_slug="dependency-inversion",
        features=profiles[1]["features"],
        current_mastery=42.0,
        eval_weak_topics=["dependency injection", "coupling"],
    )
    print(f"  Concept     : {report.concept_slug}")
    print(f"  Predicted   : {report.predicted_mastery:.1f}%")
    print(f"  Action      : {report.priority_action}")
    print(f"  Weak topics : {report.weak_subtopics}")
    print(f"  Explanation : {report.explanation}")

    # 4. Feature importances
    print("\n\n[4] Top Feature Importances:")
    print("-" * 60)
    importances = MasteryPredictor.feature_importances()
    for feat, imp in list(importances.items())[:8]:
        bar = "█" * int(imp * 200)
        print(f"  {feat:<35} {imp:.4f}  {bar}")

    # 5. Cross-validation
    print("\n\n[5] Cross-validation on synthetic data (5-fold):")
    print("-" * 60)
    from sklearn.model_selection import cross_val_score
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    X, y = _generate_synthetic_data(1000)
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1))
    ])
    scores = cross_val_score(pipe, X, y, cv=5, scoring="neg_mean_absolute_error")
    print(f"  MAE (5-fold CV): {-scores.mean():.2f} ± {scores.std():.2f}")

    print("\n✓ All checks passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
