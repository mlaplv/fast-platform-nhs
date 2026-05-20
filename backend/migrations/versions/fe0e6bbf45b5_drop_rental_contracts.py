"""drop_rental_contracts

Revision ID: fe0e6bbf45b5
Revises: 1b984146f880
Create Date: 2026-05-20 09:18:26.588685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe0e6bbf45b5'
down_revision: Union[str, Sequence[str], None] = '1b984146f880'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table('rental_contracts')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('rental_contracts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('product_base_id', sa.String(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('terms', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_base_id'], ['product_bases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

