"""neural media linker many-to-many merge v3

Revision ID: v600_neural_media_linker
Revises: v560_add_unaccent, v567_add_chat_indexes, v568_add_media_post_tracking, v569_add_short_desc, banner_v1, fb9ad52c5e5a
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = 'v600_neural_media_linker'
down_revision = ('v560_add_unaccent', 'v567_add_chat_indexes', 'v568_add_media_post_tracking', 'v569_add_short_desc', 'banner_v1', 'fb9ad52c5e5a')
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # 1. Add is_linked column to media_registry if not exists
    columns = [c['name'] for c in inspector.get_columns('media_registry')]
    if 'is_linked' not in columns:
        op.add_column('media_registry', sa.Column('is_linked', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        op.create_index('ix_media_is_linked', 'media_registry', ['tenant_id', 'is_linked'])

    # 2. Create media_usage table if not exists
    if 'media_usage' not in tables:
        op.create_table(
            'media_usage',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('asset_id', sa.String(), nullable=False),
            sa.Column('entity_id', sa.String(), nullable=False),
            sa.Column('entity_type', sa.String(length=30), nullable=False),
            sa.Column('tenant_id', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['asset_id'], ['media_registry.id'], ondelete='CASCADE'),
        )
        
        # 3. Create indexes for media_usage
        op.create_index('ix_media_usage_lookup', 'media_usage', ['entity_type', 'entity_id'])
        op.create_index('ix_media_usage_asset_entity', 'media_usage', ['asset_id', 'entity_type', 'entity_id'], unique=True)
        op.create_index('ix_media_usage_tenant', 'media_usage', ['tenant_id'])

def downgrade() -> None:
    op.drop_table('media_usage')
    op.drop_index('ix_media_is_linked', table_name='media_registry')
    op.drop_column('media_registry', 'is_linked')
