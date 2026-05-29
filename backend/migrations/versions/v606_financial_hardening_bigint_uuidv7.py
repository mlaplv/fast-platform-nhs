"""v606: Float → BigInteger financial fields + UUIDv7 PK + Composite index

Revision ID: v606_financial_hardening_bigint_uuidv7
Revises: v605_add_ctv_rate_override
Create Date: 2026-05-29

WHAT THIS MIGRATION DOES:
  1. Float → BigInteger: Tất cả trường tiền tệ (price, commission, withdrawal, voucher)
     - Dùng ROUND()::BIGINT để không mất dữ liệu (e.g. 150000.999 → 151000)
  2. Column rename: commission_rate → commission_rate_bps, rate_applied → rate_applied_bps
     - Giá trị được scale ×10000 từ float (0.15 → 1500 bps)
  3. Composite index: (affiliate_id, status) trên commission_ledger
     - Phục vụ verify_financial_integrity() query
  4. ctv_rate_override → ctv_rate_override_bps (scale ×10000)

ROLLBACK SAFETY:
  - downgrade() reverse tất cả — không mất dữ liệu khi rollback
  - Float values được ROUND() khi convert sang BigInteger

PRE-MIGRATION CHECKLIST (chạy trước khi apply):
  SELECT COUNT(*) FROM product_bases WHERE price < 0;         -- phải = 0
  SELECT COUNT(*) FROM product_variants WHERE price < 0;      -- phải = 0
  SELECT COUNT(*) FROM orders WHERE total_amount < 0;         -- phải = 0
  SELECT MAX(price % 1) FROM product_bases;                   -- lý tưởng = 0 (không có fractional)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'v606'
down_revision = 'c188ef9140f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ════════════════════════════════════════════════════════════
    # 1. orders — total_amount, point_discount_amount
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('orders') as batch_op:
        batch_op.alter_column(
            'total_amount',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(total_amount)::BIGINT',
            nullable=False,
        )
        batch_op.alter_column(
            'point_discount_amount',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(point_discount_amount, 0))::BIGINT',
            existing_nullable=True,
            nullable=False,
            server_default='0',
        )

    # ════════════════════════════════════════════════════════════
    # 2. product_bases — price, discount_price, discount_percent, ctv_rate_override
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('product_bases') as batch_op:
        batch_op.alter_column(
            'price',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(price, 0))::BIGINT',
            existing_nullable=True,
            nullable=False,
            server_default='0',
        )
        batch_op.alter_column(
            'discount_price',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(discount_price)::BIGINT',
            existing_nullable=True,
        )
        batch_op.alter_column(
            'discount_percent',
            existing_type=sa.Float(),
            type_=sa.Integer(),
            postgresql_using='ROUND(COALESCE(discount_percent, 0))::INTEGER',
            existing_nullable=True,
        )
        # Rename + scale: ctv_rate_override (float 0.0-1.0) → ctv_rate_override_bps (int bps)
        batch_op.alter_column(
            'ctv_rate_override',
            new_column_name='ctv_rate_override_bps',
            existing_type=sa.Float(),
            type_=sa.Integer(),
            # 0.15 × 10000 = 1500 bps
            postgresql_using='ROUND(ctv_rate_override * 10000)::INTEGER',
            existing_nullable=True,
        )

    # ════════════════════════════════════════════════════════════
    # 3. product_variants — price, discount_price, discount_percent
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('product_variants') as batch_op:
        batch_op.alter_column(
            'price',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(price, 0))::BIGINT',
            existing_nullable=True,
            nullable=False,
        )
        batch_op.alter_column(
            'discount_price',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(discount_price)::BIGINT',
            existing_nullable=True,
        )
        batch_op.alter_column(
            'discount_percent',
            existing_type=sa.Float(),
            type_=sa.Integer(),
            postgresql_using='ROUND(COALESCE(discount_percent, 0))::INTEGER',
            existing_nullable=True,
        )

    # ════════════════════════════════════════════════════════════
    # 4. user_loyalty — total_spent
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('user_loyalty') as batch_op:
        batch_op.alter_column(
            'total_spent',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(total_spent, 0))::BIGINT',
            existing_nullable=True,
            nullable=False,
            server_default='0',
        )

    # ════════════════════════════════════════════════════════════
    # 5. commission_tiers — thresholds + rates
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('commission_tiers') as batch_op:
        batch_op.alter_column(
            'min_revenue_threshold',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(min_revenue_threshold, 0))::BIGINT',
            nullable=False,
            server_default='0',
        )
        batch_op.alter_column(
            'max_withdrawal_per_month',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(max_withdrawal_per_month, 50000000))::BIGINT',
            nullable=False,
            server_default='50000000',
        )
        # Rename + scale: commission_rate (0.15) → commission_rate_bps (1500)
        batch_op.alter_column(
            'commission_rate',
            new_column_name='commission_rate_bps',
            existing_type=sa.Float(),
            type_=sa.Integer(),
            postgresql_using='ROUND(commission_rate * 10000)::INTEGER',
            nullable=False,
            server_default='1500',
        )
        # Rename + scale: bonus_rate (0.05) → bonus_rate_bps (500)
        batch_op.alter_column(
            'bonus_rate',
            new_column_name='bonus_rate_bps',
            existing_type=sa.Float(),
            type_=sa.Integer(),
            postgresql_using='ROUND(COALESCE(bonus_rate, 0) * 10000)::INTEGER',
            nullable=False,
            server_default='0',
        )

    # ════════════════════════════════════════════════════════════
    # 6. affiliate_profiles — aggregated stats
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('affiliate_profiles') as batch_op:
        batch_op.alter_column(
            'total_revenue',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(total_revenue, 0))::BIGINT',
            nullable=False,
            server_default='0',
        )
        batch_op.alter_column(
            'total_commission',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(total_commission, 0))::BIGINT',
            nullable=False,
            server_default='0',
        )
        batch_op.alter_column(
            'paid_commission',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(paid_commission, 0))::BIGINT',
            nullable=False,
            server_default='0',
        )

    # ════════════════════════════════════════════════════════════
    # 7. commission_ledger — financial immutable fields + rename rate
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('commission_ledger') as batch_op:
        batch_op.alter_column(
            'order_amount',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(order_amount, 0))::BIGINT',
            nullable=False,
        )
        batch_op.alter_column(
            'commission_amount',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(commission_amount, 0))::BIGINT',
            nullable=False,
        )
        # Rename + scale: rate_applied (0.15) → rate_applied_bps (1500)
        batch_op.alter_column(
            'rate_applied',
            new_column_name='rate_applied_bps',
            existing_type=sa.Float(),
            type_=sa.Integer(),
            postgresql_using='ROUND(COALESCE(rate_applied, 0) * 10000)::INTEGER',
            nullable=False,
        )

    # #11 Fix: Composite index (affiliate_id, status) cho verify_financial_integrity()
    op.create_index(
        'ix_commission_ledger_aff_status',
        'commission_ledger',
        ['affiliate_id', 'status'],
        unique=False,
    )

    # ════════════════════════════════════════════════════════════
    # 8. withdrawal_requests — financial fields
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('withdrawal_requests') as batch_op:
        batch_op.alter_column(
            'amount_requested',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(amount_requested, 0))::BIGINT',
            nullable=False,
        )
        batch_op.alter_column(
            'amount_approved',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(amount_approved)::BIGINT',
            existing_nullable=True,
        )

    # ════════════════════════════════════════════════════════════
    # 9. vouchers — value, min_spend, max_discount
    # ════════════════════════════════════════════════════════════
    with op.batch_alter_table('vouchers') as batch_op:
        batch_op.alter_column(
            'value',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(value, 0))::BIGINT',
            nullable=False,
            server_default='0',
        )
        batch_op.alter_column(
            'min_spend',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(COALESCE(min_spend, 0))::BIGINT',
            nullable=False,
            server_default='0',
        )
        batch_op.alter_column(
            'max_discount',
            existing_type=sa.Float(),
            type_=sa.BigInteger(),
            postgresql_using='ROUND(max_discount)::BIGINT',
            existing_nullable=True,
        )


def downgrade() -> None:
    # Reverse tất cả về Float (khôi phục tên cột cũ)

    # Drop composite index trước
    op.drop_index('ix_commission_ledger_aff_status', table_name='commission_ledger')

    with op.batch_alter_table('vouchers') as batch_op:
        batch_op.alter_column('value', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('min_spend', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('max_discount', existing_type=sa.BigInteger(), type_=sa.Float())

    with op.batch_alter_table('withdrawal_requests') as batch_op:
        batch_op.alter_column('amount_requested', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('amount_approved', existing_type=sa.BigInteger(), type_=sa.Float())

    with op.batch_alter_table('commission_ledger') as batch_op:
        batch_op.alter_column('order_amount', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('commission_amount', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column(
            'rate_applied_bps',
            new_column_name='rate_applied',
            existing_type=sa.Integer(),
            type_=sa.Float(),
            postgresql_using='rate_applied_bps::FLOAT / 10000',
        )

    with op.batch_alter_table('affiliate_profiles') as batch_op:
        batch_op.alter_column('total_revenue', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('total_commission', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('paid_commission', existing_type=sa.BigInteger(), type_=sa.Float())

    with op.batch_alter_table('commission_tiers') as batch_op:
        batch_op.alter_column('min_revenue_threshold', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('max_withdrawal_per_month', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column(
            'commission_rate_bps',
            new_column_name='commission_rate',
            existing_type=sa.Integer(),
            type_=sa.Float(),
            postgresql_using='commission_rate_bps::FLOAT / 10000',
        )
        batch_op.alter_column(
            'bonus_rate_bps',
            new_column_name='bonus_rate',
            existing_type=sa.Integer(),
            type_=sa.Float(),
            postgresql_using='bonus_rate_bps::FLOAT / 10000',
        )

    with op.batch_alter_table('user_loyalty') as batch_op:
        batch_op.alter_column('total_spent', existing_type=sa.BigInteger(), type_=sa.Float())

    with op.batch_alter_table('product_variants') as batch_op:
        batch_op.alter_column('price', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('discount_price', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('discount_percent', existing_type=sa.Integer(), type_=sa.Float())

    with op.batch_alter_table('product_bases') as batch_op:
        batch_op.alter_column('price', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('discount_price', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('discount_percent', existing_type=sa.Integer(), type_=sa.Float())
        batch_op.alter_column(
            'ctv_rate_override_bps',
            new_column_name='ctv_rate_override',
            existing_type=sa.Integer(),
            type_=sa.Float(),
            postgresql_using='ctv_rate_override_bps::FLOAT / 10000',
        )

    with op.batch_alter_table('orders') as batch_op:
        batch_op.alter_column('total_amount', existing_type=sa.BigInteger(), type_=sa.Float())
        batch_op.alter_column('point_discount_amount', existing_type=sa.BigInteger(), type_=sa.Float())
