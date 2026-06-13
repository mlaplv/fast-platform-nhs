"""add_seo_contextual_links

Revision ID: 2b7ff915b538
Revises: v610
Create Date: 2026-06-12 22:57:28.694091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b7ff915b538'
down_revision: Union[str, Sequence[str], None] = 'v610'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('seo_contextual_links',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('source_article_id', sa.String(), nullable=False),
    sa.Column('target_node_id', sa.String(), nullable=False),
    sa.Column('target_url', sa.String(length=1000), nullable=False),
    sa.Column('original_sentence', sa.Text(), nullable=False),
    sa.Column('linked_sentence', sa.Text(), nullable=False),
    sa.Column('anchor_text', sa.String(length=500), nullable=False),
    sa.Column('matched_entity_type', sa.Enum('PAIN_POINT', 'FEATURE', 'BRAND', 'INGREDIENT', 'SYMPTOM', name='seo_matched_entity_type_enum'), nullable=False),
    sa.Column('matched_entity_name', sa.String(length=255), nullable=False),
    sa.Column('ai_confidence', sa.Float(), nullable=False),
    sa.Column('ai_reasoning', sa.Text(), nullable=True),
    sa.Column('sentence_index', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'APPLIED', name='seo_ctx_link_status_enum'), nullable=False),
    sa.Column('reviewed_by', sa.String(), nullable=True),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('link_rel', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['source_article_id'], ['articles.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_node_id'], ['seo_nodes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_article_id', 'sentence_index', 'target_node_id', 'tenant_id', name='uq_seo_ctx_link_sentence_target')
    )
    with op.batch_alter_table('seo_contextual_links', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_seo_contextual_links_source_article_id'), ['source_article_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_seo_contextual_links_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_seo_contextual_links_target_node_id'), ['target_node_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_seo_contextual_links_tenant_id'), ['tenant_id'], unique=False)
        batch_op.create_index('ix_seo_ctx_links_source_status', ['source_article_id', 'status'], unique=False)
        batch_op.create_index('ix_seo_ctx_links_target', ['target_node_id'], unique=False)
        batch_op.create_index('ix_seo_ctx_links_tenant', ['tenant_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('seo_contextual_links', schema=None) as batch_op:
        batch_op.drop_index('ix_seo_ctx_links_tenant')
        batch_op.drop_index('ix_seo_ctx_links_target')
        batch_op.drop_index('ix_seo_ctx_links_source_status')
        batch_op.drop_index(batch_op.f('ix_seo_contextual_links_tenant_id'))
        batch_op.drop_index(batch_op.f('ix_seo_contextual_links_target_node_id'))
        batch_op.drop_index(batch_op.f('ix_seo_contextual_links_status'))
        batch_op.drop_index(batch_op.f('ix_seo_contextual_links_source_article_id'))

    op.drop_table('seo_contextual_links')
    # Drop custom enums
    op.execute("DROP TYPE seo_matched_entity_type_enum")
    op.execute("DROP TYPE seo_ctx_link_status_enum")
