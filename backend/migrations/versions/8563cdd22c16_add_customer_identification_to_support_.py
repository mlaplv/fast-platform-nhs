"""Add customer identification to support chat history

Revision ID: 8563cdd22c16
Revises: 52d25e9d745d
Create Date: 2026-04-02 15:09:40.245698

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8563cdd22c16'
down_revision: Union[str, Sequence[str], None] = '52d25e9d745d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the support_chat_history table
    op.create_table(
        'support_chat_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(), nullable=True),
        sa.Column('product_slug', sa.String(), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('customer_phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False, server_default='default'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_support_chat_history_session_id'), 'support_chat_history', ['session_id'], unique=False)
    op.create_index(op.f('ix_support_chat_history_product_slug'), 'support_chat_history', ['product_slug'], unique=False)
    op.create_index(op.f('ix_support_chat_history_tenant_id'), 'support_chat_history', ['tenant_id'], unique=False)
    op.create_index('ix_support_chat_session_created', 'support_chat_history', ['session_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('support_chat_history')
