"""Elite V2.2: Add Loyalty & Rewards System (UserLoyalty, PointTransaction, Order updates)

Revision ID: v602_add_loyalty_system
Revises: v601_add_user_profile_elite_v3
Create Date: 2026-04-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.dialects import postgresql

revision = 'v602_add_loyalty_system'
down_revision = 'e56cc76fcb74'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # 1. Update orders table
    existing_order_cols = [c['name'] for c in inspector.get_columns('orders')]
    if 'points_earned' not in existing_order_cols:
        op.add_column('orders', sa.Column('points_earned', sa.Integer(), server_default='0', nullable=False))
    if 'points_redeemed' not in existing_order_cols:
        op.add_column('orders', sa.Column('points_redeemed', sa.Integer(), server_default='0', nullable=False))
    if 'point_discount_amount' not in existing_order_cols:
        op.add_column('orders', sa.Column('point_discount_amount', sa.Numeric(precision=12, scale=2), server_default='0.0', nullable=False))

    # 2. Create user_loyalty table
    if 'user_loyalty' not in inspector.get_table_names():
        op.create_table(
            'user_loyalty',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=True),
            sa.Column('tier', sa.String(), server_default='MEMBER', nullable=False),
            sa.Column('available_points', sa.Integer(), server_default='0', nullable=False),
            sa.Column('pending_points', sa.Integer(), server_default='0', nullable=False),
            sa.Column('total_spent', sa.Numeric(precision=15, scale=2), server_default='0.0', nullable=False),
            sa.Column('tier_updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('tenant_id', sa.String(), server_default='default', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id')
        )
        op.create_index('ix_user_loyalty_tenant_id', 'user_loyalty', ['tenant_id'])

    # 3. Create point_transactions table
    if 'point_transactions' not in inspector.get_table_names():
        op.create_table(
            'point_transactions',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('order_id', sa.String(), nullable=True),
            sa.Column('amount', sa.Integer(), nullable=False),
            sa.Column('transaction_type', sa.String(), nullable=False),
            sa.Column('status', sa.String(), server_default='COMPLETED', nullable=False),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('tenant_id', sa.String(), server_default='default', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
        )
        op.create_index('ix_point_transactions_tenant_id', 'point_transactions', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('point_transactions')
    op.drop_table('user_loyalty')
    op.drop_column('orders', 'point_discount_amount')
    op.drop_column('orders', 'points_redeemed')
    op.drop_column('orders', 'points_earned')
