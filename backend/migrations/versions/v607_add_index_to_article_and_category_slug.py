"""v607: Add index to Article and Category slug

Revision ID: v607
Revises: v606
Create Date: 2026-05-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'v607'
down_revision: Union[str, Sequence[str], None] = 'ac3afa60b038'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_categories_slug',
        'categories',
        ['slug'],
        unique=False,
    )
    op.create_index(
        'ix_articles_slug',
        'articles',
        ['slug'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_articles_slug', table_name='articles')
    op.drop_index('ix_categories_slug', table_name='categories')
