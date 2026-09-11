from pydantic import BaseModel, Field
from app.models.onboarding import PathType, ExperienceLevel, CloudProvider


class OnboardingRequest(BaseModel):
    path_type: PathType
    experience: ExperienceLevel
    lld_knowledge_pct: int = Field(ge=0, le=100, default=0)
    hld_knowledge_pct: int = Field(ge=0, le=100, default=0)
    cloud_provider: CloudProvider = CloudProvider.NONE


class OnboardingResponse(BaseModel):
    is_complete: bool
    path_type: str
    experience: str
    lld_knowledge_pct: int
    hld_knowledge_pct: int
    cloud_provider: str
    curriculum_plan: list[str]
    message: str

    model_config = {"from_attributes": True}
