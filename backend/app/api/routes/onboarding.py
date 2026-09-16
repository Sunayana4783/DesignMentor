from fastapi import APIRouter
from pydantic import BaseModel
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
    """Full onboarding — called after registration."""
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


class UpdatePathRequest(BaseModel):
    path_type: str


@router.post("/update-path")
async def update_path(
    req: UpdatePathRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Called on every login — updates path_type and re-unlocks correct starting concepts."""
    from app.models.onboarding import UserOnboarding, PathType
    from app.models.curriculum import Concept
    from app.models.progress import UserProgress
    from sqlalchemy import select
    import uuid

    # Get or create onboarding
    result = await db.execute(
        select(UserOnboarding).where(UserOnboarding.user_id == current_user.id)
    )
    onboarding = result.scalar_one_or_none()

    try:
        path = PathType(req.path_type)
    except ValueError:
        path = PathType.PERSONALIZED

    if onboarding:
        onboarding.path_type = path
    else:
        onboarding = UserOnboarding(
            id=uuid.uuid4(),
            user_id=current_user.id,
            path_type=path,
            is_complete=True,
        )
        db.add(onboarding)

    await db.flush()

    # Determine first concept based on path
    # LLD only or personalized/full → start with classes-and-objects
    # HLD only → start with arch-fundamentals
    if path == PathType.HLD_ONLY:
        first_slugs = ["arch-fundamentals", "arch-tier-models", "net-ip-dns"]
    elif path == PathType.LLD_ONLY:
        first_slugs = ["classes-and-objects", "encapsulation", "inheritance"]
    else:  # personalized or full
        first_slugs = ["classes-and-objects", "encapsulation", "arch-fundamentals"]

    for slug in first_slugs:
        concept_res = await db.execute(
            select(Concept).where(Concept.slug == slug)
        )
        concept = concept_res.scalar_one_or_none()
        if not concept:
            continue
        prog_res = await db.execute(
            select(UserProgress).where(
                UserProgress.user_id == current_user.id,
                UserProgress.concept_id == concept.id,
            )
        )
        progress = prog_res.scalar_one_or_none()
        if not progress:
            db.add(UserProgress(
                user_id=current_user.id,
                concept_id=concept.id,
                is_unlocked=True,
            ))
        else:
            progress.is_unlocked = True

    await db.commit()
    return {"status": "ok", "path_type": path.value, "first_concepts": first_slugs}
