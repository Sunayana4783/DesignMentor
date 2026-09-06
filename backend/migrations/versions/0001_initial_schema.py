"""Initial schema with all tables and pgvector extension.

Revision ID: 0001
Revises:
Create Date: 2026-08-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # ── topics ───────────────────────────────────────────────────────────
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False, unique=True),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), default=0),
        sa.Column("is_active", sa.Boolean(), default=True),
    )
    op.create_index("ix_topics_slug", "topics", ["slug"])

    # ── concepts ─────────────────────────────────────────────────────────
    op.create_table(
        "concepts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("difficulty", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("content", postgresql.JSON(), nullable=False),
        sa.Column("order_index", sa.Integer(), default=0),
        sa.Column("mastery_threshold", sa.Float(), default=75.0),
        sa.Column("estimated_minutes", sa.Integer(), default=15),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_concepts_slug", "concepts", ["slug"])

    # ── concept_prerequisites ─────────────────────────────────────────────
    op.create_table(
        "concept_prerequisites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("prerequisite_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("is_required", sa.Boolean(), default=True),
    )

    # ── questions ─────────────────────────────────────────────────────────
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("question_type", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSON(), nullable=False),
        sa.Column("points", sa.Integer(), default=10),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── quiz_attempts ─────────────────────────────────────────────────────
    op.create_table(
        "quiz_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("score", sa.Float(), default=0.0),
        sa.Column("max_score", sa.Float(), default=0.0),
        sa.Column("percentage", sa.Float(), default=0.0),
        sa.Column("passed", sa.Boolean(), default=False),
        sa.Column("ai_feedback", sa.Text(), nullable=True),
        sa.Column("weak_subtopics", postgresql.JSON(), default=list),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_taken_seconds", sa.Integer(), nullable=True),
    )

    # ── user_answers ──────────────────────────────────────────────────────
    op.create_table(
        "user_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz_attempts.id"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("user_response", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), default=False),
        sa.Column("score_awarded", sa.Float(), default=0.0),
        sa.Column("ai_evaluation", sa.Text(), nullable=True),
        sa.Column("evaluation_details", postgresql.JSON(), default=dict),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── user_progress ─────────────────────────────────────────────────────
    op.create_table(
        "user_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("mastery_score", sa.Float(), default=0.0),
        sa.Column("mastery_level", sa.String(50), default="not_started"),
        sa.Column("attempts", sa.Integer(), default=0),
        sa.Column("correct_answers", sa.Integer(), default=0),
        sa.Column("total_answers", sa.Integer(), default=0),
        sa.Column("next_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_interval_days", sa.Integer(), default=1),
        sa.Column("ease_factor", sa.Float(), default=2.5),
        sa.Column("weak_subtopics", postgresql.JSON(), default=list),
        sa.Column("rf_features", postgresql.JSON(), default=dict),
        sa.Column("is_unlocked", sa.Boolean(), default=False),
        sa.Column("is_completed", sa.Boolean(), default=False),
        sa.Column("first_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_progress_user_id", "user_progress", ["user_id"])
    op.create_index("ix_user_progress_concept_id", "user_progress", ["concept_id"])

    # ── learning_sessions ─────────────────────────────────────────────────
    op.create_table(
        "learning_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("mode", sa.String(50), nullable=False),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concepts.id"), nullable=True),
        sa.Column("conversation_history", postgresql.JSON(), default=list),
        sa.Column("agent_state", postgresql.JSON(), default=dict),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
    )

    # ── design_submissions ────────────────────────────────────────────────
    op.create_table(
        "design_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("problem_slug", sa.String(200), nullable=False),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(50), nullable=False),
        sa.Column("submission_text", sa.Text(), nullable=False),
        sa.Column("review", postgresql.JSON(), default=dict),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_design_submissions_problem_slug", "design_submissions", ["problem_slug"])

    # ── interview_sessions ────────────────────────────────────────────────
    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("problem", sa.String(500), nullable=False),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("conversation_history", postgresql.JSON(), default=list),
        sa.Column("scorecard", postgresql.JSON(), default=dict),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_completed", sa.Boolean(), default=False),
    )

    # ── knowledge_chunks (RAG with pgvector) ──────────────────────────────
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_file", sa.String(500), nullable=False),
        sa.Column("concept_slug", sa.String(200), nullable=True),
        sa.Column("phase", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), default=0),
        sa.Column("token_count", sa.Integer(), default=0),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("metadata", postgresql.JSON(), default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_knowledge_chunks_concept_slug", "knowledge_chunks", ["concept_slug"])
    # Vector similarity index (IVFFlat for approximate nearest-neighbour search)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding "
        "ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("interview_sessions")
    op.drop_table("design_submissions")
    op.drop_table("learning_sessions")
    op.drop_table("user_progress")
    op.drop_table("user_answers")
    op.drop_table("quiz_attempts")
    op.drop_table("questions")
    op.drop_table("concept_prerequisites")
    op.drop_table("concepts")
    op.drop_table("topics")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
