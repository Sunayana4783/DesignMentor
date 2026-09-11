from fastapi import APIRouter
from app.core.deps import CurrentUser, DBSession
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse
from app.services.onboarding_service import OnboardingService

router = APIRouter()


@router.post("/", response_model=OnboardingResponse)
async def save_onboarding(
    req: OnboardingRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Save onboarding preferences and generate personalized curriculum."""
    return await OnboardingService.save(current_user.id, req, db)


@router.get("/", response_model=OnboardingResponse | None)
async def get_onboarding(current_user: CurrentUser, db: DBSession):
    """Get current user's onboarding data."""
    onboarding = await OnboardingService.get(current_user.id, db)
    if not onboarding:
        return None
    return OnboardingResponse(
        is_complete=onboarding.is_complete,
        path_type=onboarding.path_type.value,
        experience=onboarding.experience.value,
        lld_knowledge_pct=onboarding.lld_knowledge_pct,
        hld_knowledge_pct=onboarding.hld_knowledge_pct,
        cloud_provider=onboarding.cloud_provider.value,
        curriculum_plan=onboarding.curriculum_plan,
        message="",
    )
