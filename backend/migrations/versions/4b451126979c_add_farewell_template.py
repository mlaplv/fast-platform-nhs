"""add_farewell_template

Revision ID: 4b451126979c
Revises: v566_add_order_spam_reason
Create Date: 2026-03-06 23:13:54.355517

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision = '4b451126979c'
down_revision = 'v566_add_order_spam_reason'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('voice_profiles', sa.Column('farewell_template', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('voice_profiles', 'farewell_template')
