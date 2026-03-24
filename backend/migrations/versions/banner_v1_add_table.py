"""add banners table

Revision ID: banner_v1
Revises: system_settings_v1
Create Date: 2026-03-24 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'banner_v1'
down_revision = 'system_settings_v1'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('banners',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('image_url', sa.String(), nullable=False),
    sa.Column('link_url', sa.String(), nullable=True),
    sa.Column('position', sa.String(), nullable=False, server_default='home_main'),
    sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
    sa.Column('device_type', sa.String(), nullable=False, server_default='all'),
    sa.Column('tenant_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_banners_tenant_deleted', 'banners', ['tenant_id', 'deleted_at'])

def downgrade():
    op.drop_table('banners')
