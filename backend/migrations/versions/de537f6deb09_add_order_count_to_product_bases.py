"""add order_count to product_bases

Revision ID: de537f6deb09
Revises: 4295a9108a27
Create Date: 2026-04-08 17:44:43.687296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de537f6deb09'
down_revision: Union[str, Sequence[str], None] = '4295a9108a27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add column as nullable first
    op.add_column('product_bases', sa.Column('order_count', sa.Integer(), nullable=True))

    # 2. Backfill existing rows with 0
    op.execute("UPDATE product_bases SET order_count = 0")

    # 3. Set to NOT NULL
    op.alter_column('product_bases', 'order_count', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('product_bases', 'order_count')
