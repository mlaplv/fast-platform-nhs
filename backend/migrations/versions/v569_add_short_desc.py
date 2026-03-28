"""add product short_description

Revision ID: v569_add_short_desc
Revises: 24da2393a26a
Create Date: 2026-03-27
"""

from alembic import op
import sqlalchemy as sa

revision = 'v569_add_short_desc'
down_revision = '24da2393a26a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('product_bases', sa.Column('short_description', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column('product_bases', 'short_description')
