import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.schemas.learning import DashboardOut, ConceptProgressOut, DesignSubmitRequest, DesignReviewOut
from app.services.progress_service import ProgressService
from app.models.progress import DesignSubmission, UserProgress
from app.models.curriculum import Concept
from app.agents.orchestrator import run_agent
from app.ml.rf_model import MasteryPredictor

router = APIRouter()


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(current_user: CurrentUser, db: DBSession):
    return await ProgressService.get_dashboard(current_user.id, db)


@router.get("/concepts", response_model=list[ConceptProgressOut])
async def concept_progress(current_user: CurrentUser, db: DBSession):
    return await ProgressService.get_all_concept_progress(current_user.id, db)


@router.post("/design/submit", response_model=DesignReviewOut)
async def submit_design(
    req: DesignSubmitRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Submit a design solution for AI review."""
    initial_state = {
        "user_id":      str(current_user.id),
        "session_id":   str(uuid.uuid4()),
        "mode":         "design",
        "concept_slug": req.problem_slug,
        "user_input":   req.submission_text,
        "response_metadata": {"difficulty": req.difficulty},
        "messages":     [],
    }

    final_state = await run_agent(initial_state, db)

    submission = DesignSubmission(
        id=uuid.uuid4(),
        user_id=current_user.id,
        problem_slug=req.problem_slug,
        phase=req.phase,
        difficulty=req.difficulty,
        submission_text=req.submission_text,
        review=final_state.get("response_metadata", {}),
        overall_score=final_state.get("evaluation_score"),
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return DesignReviewOut(
        submission_id=submission.id,
        problem_slug=req.problem_slug,
        overall_score=final_state.get("evaluation_score", 0.0),
        review=final_state.get("response_metadata", {}),
        ai_feedback=final_state.get("response_message", ""),
    )


@router.get("/rf-insights/{concept_slug}")
async def rf_insights(concept_slug: str, current_user: CurrentUser, db: DBSession):
    """Return RF model predictions and feature importances for a concept."""
    concept_res = await db.execute(
        select(Concept).where(Concept.slug == concept_slug)
    )
    concept = concept_res.scalar_one_or_none()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    progress_res = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.concept_id == concept.id,
        )
    )
    progress = progress_res.scalar_one_or_none()
    features = progress.rf_features if progress else {}

    predicted_score = MasteryPredictor.predict(features)
    predicted_category = MasteryPredictor.predict_category(features)
    proba = MasteryPredictor.predict_proba(features)
    importances = MasteryPredictor.feature_importances()

    return {
        "concept_slug": concept_slug,
        "current_mastery": progress.mastery_score if progress else 0.0,
        "rf_predicted_mastery": predicted_score,
        "rf_predicted_category": predicted_category,
        "class_probabilities": proba,
        "top_feature_importances": dict(list(importances.items())[:8]),
        "features_used": features,
    }
