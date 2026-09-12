"""Convert concept category/difficulty/phase to VARCHAR to avoid enum type issues.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert category column from enum to varchar
    op.execute("""
        ALTER TABLE concepts
        ALTER COLUMN category TYPE VARCHAR(100)
        USING category::text
    """)
    # Convert difficulty column from enum to varchar
    op.execute("""
        ALTER TABLE concepts
        ALTER COLUMN difficulty TYPE VARCHAR(50)
        USING difficulty::text
    """)
    # Convert phase column in topics from enum to varchar
    op.execute("""
        ALTER TABLE topics
        ALTER COLUMN phase TYPE VARCHAR(50)
        USING phase::text
    """)


def downgrade() -> None:
    pass
