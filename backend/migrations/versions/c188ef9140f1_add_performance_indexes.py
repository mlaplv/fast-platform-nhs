"""add_performance_indexes

Revision ID: c188ef9140f1
Revises: v605
Create Date: 2026-05-28 19:56:47.592458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c188ef9140f1'
down_revision: Union[str, Sequence[str], None] = 'v605'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_inspector():
    connection = op.get_bind()
    return sa.inspect(connection)

def index_exists(inspector, table_name: str, index_name: str) -> bool:
    try:
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)
    except Exception:
        return False

def constraint_exists(inspector, table_name: str, constraint_name: str) -> bool:
    try:
        unique_constraints = inspector.get_unique_constraints(table_name)
        if any(uc['name'] == constraint_name for uc in unique_constraints):
            return True
        fk_constraints = inspector.get_foreign_keys(table_name)
        if any(fk['name'] == constraint_name for fk in fk_constraints):
            return True
    except Exception:
        pass
    return False

def drop_constraint_safe(inspector, table_name: str, constraint_name: str, type_: str = 'unique') -> None:
    if constraint_exists(inspector, table_name, constraint_name):
        try:
            op.drop_constraint(constraint_name, table_name, type_=type_)
        except Exception:
            op.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}")
    else:
        op.execute(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}")

def drop_index_safe(inspector, table_name: str, index_name: str) -> None:
    if index_exists(inspector, table_name, index_name):
        try:
            op.drop_index(index_name, table_name=table_name)
        except Exception:
            op.execute(f"DROP INDEX IF EXISTS {index_name}")

def create_index_safe(inspector, table_name: str, index_name: str, columns: list, unique: bool = False) -> None:
    if not index_exists(inspector, table_name, index_name):
        try:
            indexes = inspector.get_indexes(table_name)
            # Check if columns are already indexed in the same way under a different name
            if any(idx['column_names'] == columns and idx['unique'] == unique for idx in indexes):
                return
        except Exception:
            pass
        op.create_index(index_name, table_name, columns, unique=unique)

def recreate_foreign_key_safe(inspector, table_name: str, constraint_name: str, referred_table: str, local_cols: list, referred_cols: list) -> None:
    drop_constraint_safe(inspector, table_name, constraint_name, type_='foreignkey')
    try:
        op.create_foreign_key(None, table_name, referred_table, local_cols, referred_cols)
    except Exception:
        pass


def upgrade() -> None:
    """Upgrade schema using 2026 Elite dynamic reflection to prevent schema drift crashes."""
    inspector = get_inspector()

    # 1. Safe column alterations
    with op.batch_alter_table('product_bases', schema=None) as batch_op:
        batch_op.alter_column('ctv_rate_override',
               comment=None,
               existing_nullable=True)

    # 2. Dynamic constraint dropping (to prevent UndefinedObjectError)
    drop_constraint_safe(inspector, 'affiliate_profiles', 'affiliate_profiles_ctv_code_key', type_='unique')
    drop_constraint_safe(inspector, 'affiliate_profiles', 'affiliate_profiles_user_id_key', type_='unique')
    drop_constraint_safe(inspector, 'commission_ledger', 'commission_ledger_order_id_key', type_='unique')

    # 3. Dynamic Index drop to prepare for upgrade (if necessary)
    drop_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_ctv_code')
    drop_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_user_id')
    drop_index_safe(inspector, 'commission_ledger', 'ix_commission_ledger_order_id')

    # 4. Safe and dynamic Foreign Key recreation
    recreate_foreign_key_safe(inspector, 'affiliate_profiles', 'affiliate_profiles_commission_tier_id_fkey', 'commission_tiers', ['commission_tier_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'affiliate_profiles', 'affiliate_profiles_referred_by_ctv_id_fkey', 'affiliate_profiles', ['referred_by_ctv_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'commission_ledger', 'commission_ledger_order_id_fkey', 'orders', ['order_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'commission_ledger', 'commission_ledger_affiliate_id_fkey', 'affiliate_profiles', ['affiliate_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'withdrawal_requests', 'withdrawal_requests_admin_id_fkey', 'users', ['admin_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'withdrawal_requests', 'withdrawal_requests_affiliate_id_fkey', 'affiliate_profiles', ['affiliate_id'], ['id'])

    # 5. Safe dynamic Index creation
    create_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_ctv_code', ['ctv_code'], unique=True)
    create_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_user_id', ['user_id'], unique=True)
    create_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_tenant_id', ['tenant_id'], unique=False)
    create_index_safe(inspector, 'articles', 'ix_articles_deleted_at', ['deleted_at'], unique=False)
    create_index_safe(inspector, 'articles', 'ix_articles_status', ['status'], unique=False)
    create_index_safe(inspector, 'commission_ledger', 'ix_commission_ledger_order_id', ['order_id'], unique=True)
    create_index_safe(inspector, 'commission_ledger', 'ix_commission_ledger_status', ['status'], unique=False)
    create_index_safe(inspector, 'commission_ledger', 'ix_commission_ledger_tenant_id', ['tenant_id'], unique=False)
    create_index_safe(inspector, 'commission_tiers', 'ix_commission_tiers_tenant_id', ['tenant_id'], unique=False)
    create_index_safe(inspector, 'product_bases', 'ix_products_category_id', ['category_id'], unique=False)
    create_index_safe(inspector, 'product_bases', 'ix_products_deleted_at', ['deleted_at'], unique=False)
    create_index_safe(inspector, 'product_bases', 'ix_products_status_deleted', ['status', 'deleted_at'], unique=False)
    create_index_safe(inspector, 'product_variants', 'ix_product_variants_deleted_at', ['deleted_at'], unique=False)
    create_index_safe(inspector, 'product_variants', 'ix_product_variants_product_base_id', ['product_base_id'], unique=False)
    create_index_safe(inspector, 'vouchers', 'ix_vouchers_active_viral', ['is_active', 'is_viral'], unique=False)
    create_index_safe(inspector, 'vouchers', 'ix_vouchers_deleted_at', ['deleted_at'], unique=False)
    create_index_safe(inspector, 'vouchers', 'ix_vouchers_tenant_deleted', ['tenant_id', 'deleted_at'], unique=False)
    create_index_safe(inspector, 'withdrawal_requests', 'ix_withdrawal_requests_status', ['status'], unique=False)
    create_index_safe(inspector, 'withdrawal_requests', 'ix_withdrawal_requests_tenant_id', ['tenant_id'], unique=False)

    # 6. Audited column constraints updates
    with op.batch_alter_table('affiliate_profiles', schema=None) as batch_op:
        batch_op.alter_column('created_at', nullable=False, existing_server_default=sa.text('now()'))
        batch_op.alter_column('updated_at', nullable=False, existing_server_default=sa.text('now()'))

    with op.batch_alter_table('commission_ledger', schema=None) as batch_op:
        batch_op.alter_column('created_at', nullable=False, existing_server_default=sa.text('now()'))
        batch_op.alter_column('updated_at', nullable=False, existing_server_default=sa.text('now()'))

    with op.batch_alter_table('commission_tiers', schema=None) as batch_op:
        batch_op.alter_column('created_at', nullable=False, existing_server_default=sa.text('now()'))
        batch_op.alter_column('updated_at', nullable=False, existing_server_default=sa.text('now()'))

    with op.batch_alter_table('withdrawal_requests', schema=None) as batch_op:
        batch_op.alter_column('created_at', nullable=False, existing_server_default=sa.text('now()'))
        batch_op.alter_column('updated_at', nullable=False, existing_server_default=sa.text('now()'))


def downgrade() -> None:
    """Downgrade schema using 2026 Elite dynamic reflection to prevent schema drift crashes."""
    inspector = get_inspector()

    # 1. Safe dynamic Index dropping
    drop_index_safe(inspector, 'withdrawal_requests', 'ix_withdrawal_requests_tenant_id')
    drop_index_safe(inspector, 'withdrawal_requests', 'ix_withdrawal_requests_status')
    drop_index_safe(inspector, 'vouchers', 'ix_vouchers_tenant_deleted')
    drop_index_safe(inspector, 'vouchers', 'ix_vouchers_deleted_at')
    drop_index_safe(inspector, 'vouchers', 'ix_vouchers_active_viral')
    drop_index_safe(inspector, 'product_variants', 'ix_product_variants_product_base_id')
    drop_index_safe(inspector, 'product_variants', 'ix_product_variants_deleted_at')
    drop_index_safe(inspector, 'product_bases', 'ix_products_status_deleted')
    drop_index_safe(inspector, 'product_bases', 'ix_products_deleted_at')
    drop_index_safe(inspector, 'product_bases', 'ix_products_category_id')
    drop_index_safe(inspector, 'commission_tiers', 'ix_commission_tiers_tenant_id')
    drop_index_safe(inspector, 'commission_ledger', 'ix_commission_ledger_tenant_id')
    drop_index_safe(inspector, 'commission_ledger', 'ix_commission_ledger_status')
    drop_index_safe(inspector, 'commission_ledger', 'ix_commission_ledger_order_id')
    drop_index_safe(inspector, 'articles', 'ix_articles_status')
    drop_index_safe(inspector, 'articles', 'ix_articles_deleted_at')
    drop_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_tenant_id')
    drop_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_user_id')
    drop_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_ctv_code')

    # 2. Revert dynamic Foreign Keys to baseline
    recreate_foreign_key_safe(inspector, 'withdrawal_requests', 'withdrawal_requests_affiliate_id_fkey', 'affiliate_profiles', ['affiliate_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'withdrawal_requests', 'withdrawal_requests_admin_id_fkey', 'users', ['admin_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'commission_ledger', 'commission_ledger_affiliate_id_fkey', 'affiliate_profiles', ['affiliate_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'commission_ledger', 'commission_ledger_order_id_fkey', 'orders', ['order_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'affiliate_profiles', 'affiliate_profiles_referred_by_ctv_id_fkey', 'affiliate_profiles', ['referred_by_ctv_id'], ['id'])
    recreate_foreign_key_safe(inspector, 'affiliate_profiles', 'affiliate_profiles_commission_tier_id_fkey', 'commission_tiers', ['commission_tier_id'], ['id'])

    # 3. Restore baseline unique constraints if not present
    try:
        op.create_unique_constraint('commission_ledger_order_id_key', 'commission_ledger', ['order_id'])
    except Exception:
        pass
    try:
        op.create_unique_constraint('affiliate_profiles_user_id_key', 'affiliate_profiles', ['user_id'])
    except Exception:
        pass
    try:
        op.create_unique_constraint('affiliate_profiles_ctv_code_key', 'affiliate_profiles', ['ctv_code'])
    except Exception:
        pass

    # 4. Safe dynamic creation of unique index fallback in downgrade if needed
    create_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_user_id', ['user_id'], unique=False)
    create_index_safe(inspector, 'affiliate_profiles', 'ix_affiliate_profiles_ctv_code', ['ctv_code'], unique=False)
    create_index_safe(inspector, 'commission_ledger', 'ix_commission_ledger_order_id', ['order_id'], unique=False)

    # 5. Restore column configs to original state
    with op.batch_alter_table('withdrawal_requests', schema=None) as batch_op:
        batch_op.alter_column('updated_at', nullable=True, existing_server_default=sa.text('now()'))
        batch_op.alter_column('created_at', nullable=True, existing_server_default=sa.text('now()'))

    with op.batch_alter_table('product_bases', schema=None) as batch_op:
        batch_op.alter_column('ctv_rate_override',
               comment='Phase 2 Hybrid CTV: NULL=tier rate, 0.0=no commission, 0.2=force 20%',
               existing_nullable=True)

    with op.batch_alter_table('commission_tiers', schema=None) as batch_op:
        batch_op.alter_column('updated_at', nullable=True, existing_server_default=sa.text('now()'))
        batch_op.alter_column('created_at', nullable=True, existing_server_default=sa.text('now()'))

    with op.batch_alter_table('commission_ledger', schema=None) as batch_op:
        batch_op.alter_column('updated_at', nullable=True, existing_server_default=sa.text('now()'))
        batch_op.alter_column('created_at', nullable=True, existing_server_default=sa.text('now()'))

    with op.batch_alter_table('affiliate_profiles', schema=None) as batch_op:
        batch_op.alter_column('updated_at', nullable=True, existing_server_default=sa.text('now()'))
        batch_op.alter_column('created_at', nullable=True, existing_server_default=sa.text('now()'))
