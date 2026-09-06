"""
Random Forest Mastery Predictor.

Predicts the student's true mastery score (0-100) given a feature vector.
The model is trained on historical quiz attempt data and updated
incrementally as new data accumulates (every N attempts).

Model outputs:
  - Predicted mastery score (regression)
  - Predicted mastery category (classification): beginner/learning/developing/good/mastered
  - Feature importances (used to explain which signals matter most)
"""
import os
import joblib
import numpy as np
from pathlib import Path
from typing import Optional

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, accuracy_score
from sklearn.pipeline import Pipeline

from app.ml.features import MasteryFeatures, DIFFICULTY_MAP
from app.core.config import settings
from app.core.logging import logger


# ── Label encoding for mastery levels ────────────────────────────────────────

MASTERY_LABELS = {
    "beginner":   0,
    "learning":   1,
    "developing": 2,
    "good":       3,
    "mastered":   4,
}
MASTERY_LABELS_INV = {v: k for k, v in MASTERY_LABELS.items()}


def score_to_label(score: float) -> str:
    if score < 40:
        return "beginner"
    if score < 60:
        return "learning"
    if score < 75:
        return "developing"
    if score < 90:
        return "good"
    return "mastered"


# ── Synthetic training data generator ────────────────────────────────────────

def _generate_synthetic_data(n_samples: int = 2000) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic but realistic training data so the model
    is useful from day one before real user data accumulates.

    Relationships encoded:
    - More attempts + high correct_ratio → higher mastery
    - High score_variance + high reteach_count → lower mastery
    - Strong prerequisite mastery → higher ceiling
    - High ease_factor → faster learning
    """
    rng = np.random.default_rng(42)
    n = n_samples

    # Raw feature distributions
    attempts            = rng.integers(1, 15, n).astype(float)
    correct_ratio       = rng.beta(3, 2, n)               # skewed toward higher correct
    last_score          = rng.uniform(20, 100, n)
    best_score          = last_score + rng.uniform(0, 20, n)
    best_score          = np.clip(best_score, 0, 100)
    avg_score           = (last_score + rng.uniform(10, 80, n)) / 2
    avg_score           = np.clip(avg_score, 0, 100)
    score_trend         = last_score - avg_score
    score_variance      = rng.uniform(0, 400, n)
    total_answers       = (attempts * 5).astype(int)
    correct_answers     = (correct_ratio * total_answers).astype(int)
    weak_topic_count    = rng.integers(0, 5, n).astype(float)
    reteach_count       = rng.integers(0, 4, n).astype(float)
    avg_time            = rng.exponential(30, n)
    days_first          = rng.uniform(0, 60, n)
    days_last           = rng.uniform(0, 14, n)
    ease_factor         = rng.uniform(1.3, 3.0, n)
    review_interval     = rng.integers(1, 30, n).astype(float)
    concept_difficulty  = rng.integers(0, 4, n).astype(float)
    prereq_mastery      = rng.beta(4, 2, n) * 100
    phase               = rng.integers(0, 3, n).astype(float)
    mode_dist_quiz      = rng.beta(2, 2, n)
    consecutive_correct = rng.integers(0, 10, n).astype(float)

    X = np.column_stack([
        attempts, avg_score, last_score, best_score, score_trend,
        score_variance, correct_ratio, total_answers, correct_answers,
        weak_topic_count, reteach_count, avg_time, days_first, days_last,
        ease_factor, review_interval, concept_difficulty, prereq_mastery,
        phase, mode_dist_quiz, consecutive_correct,
    ]).astype(np.float32)

    # Realistic mastery score formula
    y = (
        0.30 * avg_score
        + 0.25 * correct_ratio * 100
        + 0.15 * (attempts / 15) * 100
        + 0.10 * prereq_mastery
        + 0.05 * (ease_factor / 3.0) * 100
        - 0.08 * (weak_topic_count / 5) * 100
        - 0.07 * (reteach_count / 4) * 100
    )
    y = np.clip(y, 0, 100).astype(np.float32)

    return X, y


# ── Model class ───────────────────────────────────────────────────────────────

class MasteryPredictor:
    """
    Wrapper around two scikit-learn Random Forest models:
    - regressor:   predicts mastery score (0-100)
    - classifier:  predicts mastery category (beginner/learning/developing/good/mastered)

    Both wrapped in a Pipeline with StandardScaler.
    """

    _regressor:  Optional[Pipeline] = None
    _classifier: Optional[Pipeline] = None
    _model_path_reg: str = ""
    _model_path_clf: str = ""
    _feature_importances: Optional[dict] = None

    # ── Initialise / load ─────────────────────────────────────────────────

    @classmethod
    def load_or_init(cls) -> None:
        """Load saved models from disk, or train from synthetic data if absent."""
        cls._model_path_reg = os.path.join(
            os.path.dirname(__file__), "models", "rf_regressor.pkl"
        )
        cls._model_path_clf = os.path.join(
            os.path.dirname(__file__), "models", "rf_classifier.pkl"
        )

        if Path(cls._model_path_reg).exists() and Path(cls._model_path_clf).exists():
            cls._regressor  = joblib.load(cls._model_path_reg)
            cls._classifier = joblib.load(cls._model_path_clf)
            logger.info("rf_model_loaded_from_disk")
        else:
            logger.info("rf_model_training_from_synthetic_data")
            cls._train_from_scratch()

    # ── Training ──────────────────────────────────────────────────────────

    @classmethod
    def _train_from_scratch(cls) -> None:
        X, y = _generate_synthetic_data(n_samples=3000)
        y_labels = np.array([MASTERY_LABELS[score_to_label(s)] for s in y])
        cls._fit(X, y, y_labels)
        cls._save()

    @classmethod
    def _fit(
        cls,
        X: np.ndarray,
        y_reg: np.ndarray,
        y_clf: np.ndarray,
    ) -> None:
        """Build and fit both pipelines."""
        # ── Regressor ──────────────────────────────────────────────────
        rf_reg = RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features="sqrt",
            n_jobs=-1,
            random_state=42,
            oob_score=True,
        )
        cls._regressor = Pipeline([
            ("scaler", StandardScaler()),
            ("rf",     rf_reg),
        ])
        cls._regressor.fit(X, y_reg)

        # ── Classifier ─────────────────────────────────────────────────
        rf_clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features="sqrt",
            n_jobs=-1,
            random_state=42,
            class_weight="balanced",
            oob_score=True,
        )
        cls._classifier = Pipeline([
            ("scaler", StandardScaler()),
            ("rf",     rf_clf),
        ])
        cls._classifier.fit(X, y_clf)

        # Feature importances from regressor
        importances = cls._regressor.named_steps["rf"].feature_importances_
        cols = MasteryFeatures.column_names()
        cls._feature_importances = dict(
            sorted(zip(cols, importances), key=lambda x: -x[1])
        )

        oob_reg = cls._regressor.named_steps["rf"].oob_score_
        oob_clf = cls._classifier.named_steps["rf"].oob_score_
        logger.info(
            "rf_model_trained",
            n_samples=len(X),
            oob_reg_r2=round(float(oob_reg), 4),
            oob_clf_acc=round(float(oob_clf), 4),
        )

    # ── Prediction ────────────────────────────────────────────────────────

    @classmethod
    def predict(cls, features: dict) -> float:
        """
        Predict mastery score (0-100) from a features dict.
        Returns 0.0 gracefully if model is not loaded or features are empty.
        """
        if cls._regressor is None:
            cls.load_or_init()
        if not features:
            return 0.0
        try:
            feat = MasteryFeatures.from_dict(features)
            X = feat.to_array().reshape(1, -1)
            score = float(cls._regressor.predict(X)[0])
            return round(np.clip(score, 0.0, 100.0), 2)
        except Exception as exc:
            logger.warning("rf_predict_failed", error=str(exc))
            return 0.0

    @classmethod
    def predict_category(cls, features: dict) -> str:
        """Predict mastery category label."""
        if cls._classifier is None:
            cls.load_or_init()
        if not features:
            return "not_started"
        try:
            feat = MasteryFeatures.from_dict(features)
            X = feat.to_array().reshape(1, -1)
            label_idx = int(cls._classifier.predict(X)[0])
            return MASTERY_LABELS_INV.get(label_idx, "beginner")
        except Exception as exc:
            logger.warning("rf_classify_failed", error=str(exc))
            return "beginner"

    @classmethod
    def predict_proba(cls, features: dict) -> dict[str, float]:
        """Predict probability for each mastery category."""
        if cls._classifier is None:
            cls.load_or_init()
        if not features:
            return {k: 0.0 for k in MASTERY_LABELS}
        try:
            feat = MasteryFeatures.from_dict(features)
            X = feat.to_array().reshape(1, -1)
            proba = cls._classifier.predict_proba(X)[0]
            classes = cls._classifier.named_steps["rf"].classes_
            return {
                MASTERY_LABELS_INV.get(int(c), str(c)): round(float(p), 4)
                for c, p in zip(classes, proba)
            }
        except Exception as exc:
            logger.warning("rf_proba_failed", error=str(exc))
            return {}

    @classmethod
    def feature_importances(cls) -> dict[str, float]:
        if cls._feature_importances is None:
            return {}
        return cls._feature_importances

    # ── Persistence ───────────────────────────────────────────────────────

    @classmethod
    def _save(cls) -> None:
        os.makedirs(os.path.dirname(cls._model_path_reg), exist_ok=True)
        joblib.dump(cls._regressor,  cls._model_path_reg,  compress=3)
        joblib.dump(cls._classifier, cls._model_path_clf,  compress=3)
        logger.info("rf_model_saved", reg=cls._model_path_reg, clf=cls._model_path_clf)

    # ── Incremental retraining ─────────────────────────────────────────────

    @classmethod
    def retrain(cls, X_new: np.ndarray, y_reg_new: np.ndarray) -> dict:
        """
        Retrain the model from scratch combining synthetic + real data.
        Called by the retraining service when enough new data accumulates.
        """
        X_synth, y_synth = _generate_synthetic_data(n_samples=1000)

        # Combine synthetic base with real data (real data weighted 3x)
        X_combined = np.vstack([X_synth, X_new, X_new, X_new])
        y_combined  = np.concatenate([y_synth, y_reg_new, y_reg_new, y_reg_new])
        y_labels    = np.array([MASTERY_LABELS[score_to_label(s)] for s in y_combined])

        cls._fit(X_combined, y_combined, y_labels)
        cls._save()

        # Evaluate on real data only
        y_pred = cls._regressor.predict(X_new)
        mae = float(mean_absolute_error(y_reg_new, y_pred))

        return {
            "retrained": True,
            "real_samples": len(X_new),
            "total_samples": len(X_combined),
            "mae_on_real": round(mae, 2),
            "feature_importances": cls._feature_importances,
        }
