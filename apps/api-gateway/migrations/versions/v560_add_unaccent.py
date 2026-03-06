"""V56.0: Add unaccent extension for Vietnamese search

Revision ID: v560_add_unaccent
Revises: a1b2c3d4e5f6
Create Date: 2026-03-06 12:30:00.000000+00:00
"""
from alembic import op

# revision identifiers
revision = "v560_add_unaccent"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
