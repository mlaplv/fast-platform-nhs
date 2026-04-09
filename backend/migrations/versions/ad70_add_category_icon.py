"""add category icon

Revision ID: ad70_add_category_icon
Revises: de537f6deb09
Create Date: 2026-04-09 16:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad70_add_category_icon'
down_revision: Union[str, Sequence[str], None] = 'de537f6deb09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('categories', sa.Column('icon', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('categories', 'icon')
