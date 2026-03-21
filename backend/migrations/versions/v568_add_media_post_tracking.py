"""add media post tracking columns

Revision ID: v568_add_media_post_tracking
Revises: v567_add_chat_indexes
Create Date: 2026-03-20
"""

from alembic import op
import sqlalchemy as sa

revision = 'v568_add_media_post_tracking'
down_revision = 'dec3153f46c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('media_registry', sa.Column('linked_post_id', sa.String(), nullable=True))
    op.add_column('media_registry', sa.Column('linked_post_type', sa.String(30), nullable=True))
    op.create_index('ix_media_linked_post', 'media_registry', ['linked_post_type', 'linked_post_id'])


def downgrade() -> None:
    op.drop_index('ix_media_linked_post', table_name='media_registry')
    op.drop_column('media_registry', 'linked_post_type')
    op.drop_column('media_registry', 'linked_post_id')
