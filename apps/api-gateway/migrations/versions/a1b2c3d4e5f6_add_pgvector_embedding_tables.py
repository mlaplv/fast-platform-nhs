"""Add pgvector embedding tables for RAG

Revision ID: a1b2c3d4e5f6
Revises: c1d32faf40b8
Create Date: 2026-03-05 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'c1d32faf40b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Product embeddings: drop old Text column, add vector and content_hash
    op.execute('ALTER TABLE product_embeddings DROP COLUMN embedding')
    op.execute('ALTER TABLE product_embeddings ADD COLUMN embedding vector(384)')
    op.add_column('product_embeddings', sa.Column('content_hash', sa.String(64), nullable=True))
    op.create_index('ix_product_embeddings_ivfflat', 'product_embeddings', ['embedding'], postgresql_using='ivfflat', postgresql_with={'lists': 10}, postgresql_ops={'embedding': 'vector_cosine_ops'})

    # Article embeddings
    op.execute('ALTER TABLE article_embeddings DROP COLUMN embedding')
    op.execute('ALTER TABLE article_embeddings ADD COLUMN embedding vector(384)')
    op.add_column('article_embeddings', sa.Column('content_hash', sa.String(64), nullable=True))
    op.create_index('ix_article_embeddings_ivfflat', 'article_embeddings', ['embedding'], postgresql_using='ivfflat', postgresql_with={'lists': 10}, postgresql_ops={'embedding': 'vector_cosine_ops'})


def downgrade() -> None:
    op.drop_index('ix_article_embeddings_ivfflat', table_name='article_embeddings')
    op.drop_column('article_embeddings', 'content_hash')
    op.execute('ALTER TABLE article_embeddings DROP COLUMN embedding')
    op.add_column('article_embeddings', sa.Column('embedding', sa.Text(), nullable=True))
    
    op.drop_index('ix_product_embeddings_ivfflat', table_name='product_embeddings')
    op.drop_column('product_embeddings', 'content_hash')
    op.execute('ALTER TABLE product_embeddings DROP COLUMN embedding')
    op.add_column('product_embeddings', sa.Column('embedding', sa.Text(), nullable=True))
    
    op.execute('DROP EXTENSION IF EXISTS vector')
