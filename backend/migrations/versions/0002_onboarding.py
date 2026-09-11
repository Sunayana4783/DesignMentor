"""Add user onboarding table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_onboarding",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("path_type", sa.String(50), nullable=False, default="personalized"),
        sa.Column("experience", sa.String(50), nullable=False, default="fresher"),
        sa.Column("lld_knowledge_pct", sa.Integer(), default=0),
        sa.Column("hld_knowledge_pct", sa.Integer(), default=0),
        sa.Column("cloud_provider", sa.String(50), default="none"),
        sa.Column("curriculum_plan", postgresql.JSON(), default=list),
        sa.Column("is_complete", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_onboarding_user_id", "user_onboarding", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_onboarding")
