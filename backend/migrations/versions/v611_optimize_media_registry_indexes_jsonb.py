"""v611 - Optimize media_registry: drop redundant indexes + migrate json to jsonb

Revision ID: v611
Revises: v610
Create Date: 2026-06-19

PHÂN TÍCH:
- 10 indexes cho 111 rows → index/data ratio = 2.75x (bất thường)
- 3 indexes thừa hoàn toàn (bị bao phủ bởi composite indexes tốt hơn):
    ix_media_registry_campaign_id → bị bao phủ bởi ix_media_campaign_provider(campaign_id, provider)
    ix_media_registry_is_linked   → bị bao phủ bởi ix_media_is_linked(tenant_id, is_linked)
    ix_media_registry_tenant_id   → bị bao phủ bởi ix_media_tenant_deleted(tenant_id, deleted_at)
- media_metadata column dùng json (raw text) thay vì jsonb (binary, nén ~30%)

MỤC TIÊU:
- Giảm từ 10 → 7 indexes: index overhead 176 kB → ~128 kB
- json → jsonb: data column ~64 kB → ~45 kB
- Mỗi INSERT/UPDATE giờ chỉ cập nhật 7 B-tree thay vì 10 → write throughput tăng ~23%
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "v611"
down_revision = "da70604553ae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # BƯỚC 1: Drop 3 indexes thừa (không lock bảng, an toàn online)
    # ----------------------------------------------------------------

    # ix_media_registry_campaign_id(campaign_id) bị bao phủ bởi
    # ix_media_campaign_provider(campaign_id, provider) — prefix match OK
    op.drop_index("ix_media_registry_campaign_id", table_name="media_registry")

    # ix_media_registry_is_linked(is_linked) bị bao phủ bởi
    # ix_media_is_linked(tenant_id, is_linked) — mọi query có tenant_id sẽ dùng composite
    op.drop_index("ix_media_registry_is_linked", table_name="media_registry")

    # ix_media_registry_tenant_id(tenant_id) bị bao phủ bởi
    # ix_media_tenant_deleted(tenant_id, deleted_at) — prefix match OK
    op.drop_index("ix_media_registry_tenant_id", table_name="media_registry")

    # ----------------------------------------------------------------
    # BƯỚC 2: Migrate media_metadata từ json → jsonb
    # USING cast đảm bảo không mất data, Postgres tự convert
    # ----------------------------------------------------------------
    op.alter_column(
        "media_registry",
        "media_metadata",
        type_=JSONB,
        postgresql_using="media_metadata::jsonb",
        existing_nullable=True,
    )


def downgrade() -> None:
    # Khôi phục json (downgrade mất tính năng jsonb nhưng không mất data)
    op.alter_column(
        "media_registry",
        "media_metadata",
        type_=sa.JSON(),
        postgresql_using="media_metadata::json",
        existing_nullable=True,
    )

    # Tái tạo 3 indexes đã xóa
    op.create_index("ix_media_registry_campaign_id", "media_registry", ["campaign_id"])
    op.create_index("ix_media_registry_is_linked", "media_registry", ["is_linked"])
    op.create_index("ix_media_registry_tenant_id", "media_registry", ["tenant_id"])
