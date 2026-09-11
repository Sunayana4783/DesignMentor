import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class PathType(str, enum.Enum):
    LLD_ONLY = "lld_only"
    HLD_ONLY = "hld_only"
    PERSONALIZED = "personalized"
    FULL = "full"


class ExperienceLevel(str, enum.Enum):
    FRESHER = "fresher"
    ONE_YEAR = "1yr"
    TWO_YEARS = "2yr"
    THREE_YEARS = "3yr"
    FOUR_YEARS = "4yr"
    FIVE_PLUS = "5yr+"


class CloudProvider(str, enum.Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    NONE = "none"
    OTHER = "other"


class UserOnboarding(Base):
    """Stores user's learning preferences collected during onboarding."""
    __tablename__ = "user_onboarding"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Learning path choice
    path_type: Mapped[PathType] = mapped_column(Enum(PathType), nullable=False, default=PathType.PERSONALIZED)

    # Experience level
    experience: Mapped[ExperienceLevel] = mapped_column(Enum(ExperienceLevel), nullable=False, default=ExperienceLevel.FRESHER)

    # Self-assessed knowledge percentage (0-100)
    lld_knowledge_pct: Mapped[int] = mapped_column(Integer, default=0)   # How much LLD they already know
    hld_knowledge_pct: Mapped[int] = mapped_column(Integer, default=0)   # How much HLD they already know

    # Cloud provider preference
    cloud_provider: Mapped[CloudProvider] = mapped_column(Enum(CloudProvider), default=CloudProvider.NONE)

    # Generated personalized curriculum plan (list of concept slugs in order)
    curriculum_plan: Mapped[list] = mapped_column(JSON, default=list)

    # Whether onboarding is complete
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="onboarding")

    def __repr__(self) -> str:
        return f"<UserOnboarding user={self.user_id} path={self.path_type}>"
