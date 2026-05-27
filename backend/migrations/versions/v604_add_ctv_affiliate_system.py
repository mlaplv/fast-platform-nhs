"""Viral 2026: Add CTV/Affiliate System (commission_tiers, affiliate_profiles, commission_ledger, withdrawal_requests, orders CTV fields)

Revision ID: v604_add_ctv_affiliate_system
Revises: v603_add_category_metadata
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.dialects import postgresql

revision = 'v604_add_ctv_affiliate_system'
down_revision = 'd7e402929cea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # ── 1. commission_tiers ────────────────────────────────────────────────────
    if 'commission_tiers' not in existing_tables:
        op.create_table(
            'commission_tiers',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('min_revenue_threshold', sa.Float(), server_default='0', nullable=False),
            sa.Column('commission_rate', sa.Float(), server_default='0.15', nullable=False),
            sa.Column('bonus_rate', sa.Float(), server_default='0', nullable=False),
            sa.Column('max_withdrawal_per_month', sa.Float(), server_default='50000000', nullable=False),
            sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('tenant_id', sa.String(), server_default='default', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_commission_tiers_tenant_deleted', 'commission_tiers', ['tenant_id', 'deleted_at'])
        op.create_index('ix_commission_tiers_is_default', 'commission_tiers', ['is_default'])

        # Seed: Default tier — Đồng 15%
        op.execute("""
            INSERT INTO commission_tiers
                (id, name, min_revenue_threshold, commission_rate, bonus_rate,
                 max_withdrawal_per_month, is_default, tenant_id, created_at, updated_at)
            VALUES
                (gen_random_uuid()::text, 'Đồng', 0, 0.15, 0, 50000000, true, 'default', now(), now()),
                (gen_random_uuid()::text, 'Bạc', 50000000, 0.17, 0, 100000000, false, 'default', now(), now()),
                (gen_random_uuid()::text, 'Vàng', 200000000, 0.20, 0, 200000000, false, 'default', now(), now()),
                (gen_random_uuid()::text, 'Kim Cương', 1000000000, 0.25, 0.02, 500000000, false, 'default', now(), now())
        """)

    # ── 2. affiliate_profiles ─────────────────────────────────────────────────
    if 'affiliate_profiles' not in existing_tables:
        op.create_table(
            'affiliate_profiles',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('ctv_code', sa.String(20), nullable=False),
            sa.Column('status', sa.String(20), server_default='ACTIVE', nullable=False),
            sa.Column('commission_tier_id', sa.String(), nullable=True),
            sa.Column('total_revenue', sa.Float(), server_default='0', nullable=False),
            sa.Column('total_commission', sa.Float(), server_default='0', nullable=False),
            sa.Column('paid_commission', sa.Float(), server_default='0', nullable=False),
            sa.Column('total_orders', sa.Integer(), server_default='0', nullable=False),
            sa.Column('balance_seal', sa.Text(), nullable=True),
            sa.Column('referral_chain_depth', sa.Integer(), server_default='0', nullable=False),
            sa.Column('referred_by_ctv_id', sa.String(), nullable=True),
            sa.Column('bank_info_enc', sa.Text(), nullable=True),
            sa.Column('tenant_id', sa.String(), server_default='default', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['commission_tier_id'], ['commission_tiers.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['referred_by_ctv_id'], ['affiliate_profiles.id'], ondelete='SET NULL'),
            sa.UniqueConstraint('user_id'),
            sa.UniqueConstraint('ctv_code'),
        )
        op.create_index('ix_affiliate_profiles_user_id', 'affiliate_profiles', ['user_id'])
        op.create_index('ix_affiliate_profiles_ctv_code', 'affiliate_profiles', ['ctv_code'])
        op.create_index('ix_affiliate_profiles_status', 'affiliate_profiles', ['status', 'tenant_id'])
        op.create_index('ix_affiliate_profiles_tenant_deleted', 'affiliate_profiles', ['tenant_id', 'deleted_at'])

    # ── 3. commission_ledger ──────────────────────────────────────────────────
    if 'commission_ledger' not in existing_tables:
        op.create_table(
            'commission_ledger',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('affiliate_id', sa.String(), nullable=False),
            sa.Column('order_id', sa.String(), nullable=False),
            sa.Column('order_amount', sa.Float(), nullable=False),
            sa.Column('commission_amount', sa.Float(), nullable=False),
            sa.Column('rate_applied', sa.Float(), nullable=False),
            sa.Column('tier_snapshot', postgresql.JSONB(), nullable=True),
            sa.Column('status', sa.String(20), server_default='PENDING', nullable=False),
            sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('admin_note', sa.Text(), nullable=True),
            sa.Column('integrity_token', sa.Text(), nullable=True),
            sa.Column('tenant_id', sa.String(), server_default='default', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['affiliate_id'], ['affiliate_profiles.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='RESTRICT'),
            sa.UniqueConstraint('order_id'),  # Idempotency guard
        )
        op.create_index('ix_commission_ledger_affiliate_id', 'commission_ledger', ['affiliate_id'])
        op.create_index('ix_commission_ledger_order_id', 'commission_ledger', ['order_id'])
        op.create_index('ix_commission_ledger_tenant_status', 'commission_ledger', ['tenant_id', 'status'])
        op.create_index('ix_commission_ledger_affiliate_created', 'commission_ledger', ['affiliate_id', 'created_at'])

    # ── 4. withdrawal_requests ────────────────────────────────────────────────
    if 'withdrawal_requests' not in existing_tables:
        op.create_table(
            'withdrawal_requests',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('affiliate_id', sa.String(), nullable=False),
            sa.Column('amount_requested', sa.Float(), nullable=False),
            sa.Column('amount_approved', sa.Float(), nullable=True),
            sa.Column('bank_snapshot_enc', sa.Text(), nullable=True),
            sa.Column('status', sa.String(20), server_default='PENDING', nullable=False),
            sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('admin_id', sa.String(), nullable=True),
            sa.Column('admin_note', sa.Text(), nullable=True),
            sa.Column('integrity_token', sa.Text(), nullable=True),
            sa.Column('tenant_id', sa.String(), server_default='default', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['affiliate_id'], ['affiliate_profiles.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        )
        op.create_index('ix_withdrawal_requests_affiliate_id', 'withdrawal_requests', ['affiliate_id'])
        op.create_index('ix_withdrawal_requests_tenant_status', 'withdrawal_requests', ['tenant_id', 'status'])

    # ── 5. Add CTV attribution columns to orders ──────────────────────────────
    existing_order_cols = [c['name'] for c in inspector.get_columns('orders')]
    if 'ctv_code' not in existing_order_cols:
        op.add_column('orders', sa.Column('ctv_code', sa.String(20), nullable=True))
        op.create_index('ix_orders_ctv_code', 'orders', ['ctv_code'])
    if 'ctv_affiliate_id' not in existing_order_cols:
        op.add_column('orders', sa.Column('ctv_affiliate_id', sa.String(), nullable=True))
        op.create_index('ix_orders_ctv_affiliate_id', 'orders', ['ctv_affiliate_id'])
    if 'attribution_source' not in existing_order_cols:
        op.add_column('orders', sa.Column('attribution_source', sa.String(20), nullable=True))


def downgrade() -> None:
    # Orders cleanup
    op.drop_index('ix_orders_ctv_code', 'orders')
    op.drop_index('ix_orders_ctv_affiliate_id', 'orders')
    op.drop_column('orders', 'attribution_source')
    op.drop_column('orders', 'ctv_affiliate_id')
    op.drop_column('orders', 'ctv_code')
    # Tables
    op.drop_table('withdrawal_requests')
    op.drop_table('commission_ledger')
    op.drop_table('affiliate_profiles')
    op.drop_table('commission_tiers')
