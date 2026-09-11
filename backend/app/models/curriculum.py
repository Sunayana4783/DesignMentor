import uuid
from datetime import datetime
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Enum, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.db.base import Base


class Phase(str, enum.Enum):
    FOUNDATION = "foundation"
    LLD = "lld"
    HLD = "hld"


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ConceptCategory(str, enum.Enum):
    # LLD
    OOP = "oop"
    SOLID = "solid"
    DESIGN_PRINCIPLES = "design_principles"
    CREATIONAL_PATTERNS = "creational_patterns"
    STRUCTURAL_PATTERNS = "structural_patterns"
    BEHAVIORAL_PATTERNS = "behavioral_patterns"
    LLD_PROBLEMS = "lld_problems"
    # HLD — Architecture
    ARCHITECTURE = "architecture"
    # HLD — Networking & APIs
    NETWORKING = "networking"
    # HLD — Databases
    DATABASES = "databases"
    # HLD — Caching
    CACHING = "caching"
    # HLD — General
    SYSTEM_DESIGN_BASICS = "system_design_basics"
    DISTRIBUTED_SYSTEMS = "distributed_systems"
    HLD_COMPONENTS = "hld_components"
    HLD_PROBLEMS = "hld_problems"


class Topic(Base):
    """Top-level grouping: LLD, HLD, Foundation."""
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    phase: Mapped[Phase] = mapped_column(Enum(Phase), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    concepts: Mapped[list["Concept"]] = relationship(back_populates="topic")

    def __repr__(self) -> str:
        return f"<Topic {self.name}>"


class Concept(Base):
    """Individual learnable concept (e.g., Singleton, Caching, CAP Theorem)."""
    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    category: Mapped[ConceptCategory] = mapped_column(Enum(ConceptCategory), nullable=False)
    difficulty: Mapped[DifficultyLevel] = mapped_column(Enum(DifficultyLevel), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Rich content: explanation, examples, code snippets, analogies stored as JSON
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    mastery_threshold: Mapped[float] = mapped_column(Float, default=75.0)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    topic: Mapped["Topic"] = relationship(back_populates="concepts")
    prerequisites: Mapped[list["ConceptPrerequisite"]] = relationship(
        foreign_keys="ConceptPrerequisite.concept_id", back_populates="concept"
    )
    dependents: Mapped[list["ConceptPrerequisite"]] = relationship(
        foreign_keys="ConceptPrerequisite.prerequisite_id", back_populates="prerequisite"
    )
    questions: Mapped[list["Question"]] = relationship(back_populates="concept")
    user_progress: Mapped[list["UserProgress"]] = relationship(back_populates="concept")

    def __repr__(self) -> str:
        return f"<Concept {self.name}>"


class ConceptPrerequisite(Base):
    """Knowledge graph edges: concept -> prerequisite."""
    __tablename__ = "concept_prerequisites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    prerequisite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)

    concept: Mapped["Concept"] = relationship(foreign_keys=[concept_id], back_populates="prerequisites")
    prerequisite: Mapped["Concept"] = relationship(foreign_keys=[prerequisite_id], back_populates="dependents")
