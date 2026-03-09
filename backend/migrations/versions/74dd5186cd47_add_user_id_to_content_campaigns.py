"""add user_id to content_campaigns

Revision ID: 74dd5186cd47
Revises: dc1b7529149e
Create Date: 2026-03-09 06:31:31.456473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74dd5186cd47'
down_revision: Union[str, Sequence[str], None] = 'dc1b7529149e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('content_campaigns', sa.Column('user_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_campaigns_user', 'content_campaigns', 'users', ['user_id'], ['id'])
    op.create_index('ix_campaigns_user_id', 'content_campaigns', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_campaigns_user_id', table_name='content_campaigns')
    op.drop_constraint('fk_campaigns_user', 'content_campaigns', type_='foreignkey')
    op.drop_column('content_campaigns', 'user_id')
