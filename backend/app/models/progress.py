import uuid
from datetime import datetime
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Enum, JSON, func, Date
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.db.base import Base


class MasteryLevel(str, enum.Enum):
    NOT_STARTED = "not_started"
    BEGINNER = "beginner"       # 0-40%
    LEARNING = "learning"       # 40-60%
    DEVELOPING = "developing"   # 60-75%
    GOOD = "good"               # 75-90%
    MASTERED = "mastered"       # 90-100%


class UserProgress(Base):
    """Tracks mastery per user per concept — the core student memory."""
    __tablename__ = "user_progress"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    concept_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("concepts.id"), nullable=False, index=True)

    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)   # 0-100
    mastery_level: Mapped[MasteryLevel] = mapped_column(
        Enum(MasteryLevel), default=MasteryLevel.NOT_STARTED
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    total_answers: Mapped[int] = mapped_column(Integer, default=0)

    # Spaced repetition fields
    next_review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_interval_days: Mapped[int] = mapped_column(Integer, default=1)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)     # SM-2 algorithm ease

    # Weak subtopics within the concept
    weak_subtopics: Mapped[list] = mapped_column(JSON, default=list)

    # RF model prediction features (stored for incremental training)
    rf_features: Mapped[dict] = mapped_column(JSON, default=dict)

    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    first_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="progress_records")
    concept: Mapped["Concept"] = relationship(back_populates="user_progress")

    def __repr__(self) -> str:
        return f"<UserProgress user={self.user_id} concept={self.concept_id} mastery={self.mastery_score}%>"


class LearningSession(Base):
    """A single learn/quiz/practice session."""
    __tablename__ = "learning_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)   # learn, quiz, design, interview, revision
    concept_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("concepts.id"), nullable=True)
    # Full conversation history stored as JSON array
    conversation_history: Mapped[list] = mapped_column(JSON, default=list)
    # Agent state snapshot
    agent_state: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="learning_sessions")


class DesignSubmission(Base):
    """User's design answer for LLD/HLD problem."""
    __tablename__ = "design_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    problem_slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)   # lld / hld
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    submission_text: Mapped[str] = mapped_column(Text, nullable=False)
    # Structured review from Design Reviewer Agent
    review: Mapped[dict] = mapped_column(JSON, default=dict)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="design_submissions")


class InterviewSession(Base):
    """Interview mode session."""
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    problem: Mapped[str] = mapped_column(String(500), nullable=False)
    phase: Mapped[str] = mapped_column(String(50), nullable=False)
    conversation_history: Mapped[list] = mapped_column(JSON, default=list)
    # Final scorecard from Interview Agent
    scorecard: Mapped[dict] = mapped_column(JSON, default=dict)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="interview_sessions")
