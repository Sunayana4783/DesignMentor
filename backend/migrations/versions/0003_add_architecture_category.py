"""Add ARCHITECTURE to conceptcategory enum.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-05
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE to add enum values
    op.execute("ALTER TYPE conceptcategory ADD VALUE IF NOT EXISTS 'architecture'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values easily — no-op
    pass
