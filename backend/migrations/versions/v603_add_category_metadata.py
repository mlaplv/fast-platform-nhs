"""add category metadata

Revision ID: v603_add_category_metadata
Revises: v602_add_loyalty_system
Create Date: 2026-04-20 12:47:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'v603_add_category_metadata'
down_revision = 'db1b72b4063d'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('categories', sa.Column('category_metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))

def downgrade() -> None:
    op.drop_column('categories', 'category_metadata')
