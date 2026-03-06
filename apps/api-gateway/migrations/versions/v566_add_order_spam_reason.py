"""add_order_spam_reason

Revision ID: v566_add_order_spam_reason
Revises: e017ee064b11
Create Date: 2026-03-06 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'v566_add_order_spam_reason'
down_revision: Union[str, Sequence[str], None] = 'e017ee064b11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('orders', sa.Column('spam_reason', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'spam_reason')
