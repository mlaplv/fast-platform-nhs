"""
v605_add_ctv_rate_override.py
Phase 2: Per-product CTV commission rate override.
Hybrid Priority Chain: product override -> tier rate -> system default.
"""
from alembic import op
import sqlalchemy as sa

revision = 'v605'
down_revision = 'v604_add_ctv_affiliate_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'product_bases',
        sa.Column(
            'ctv_rate_override',
            sa.Float(),
            nullable=True,
            comment='Phase 2 Hybrid CTV: NULL=tier rate, 0.0=no commission, 0.2=force 20%'
        )
    )


def downgrade() -> None:
    op.drop_column('product_bases', 'ctv_rate_override')
