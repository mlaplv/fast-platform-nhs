from typing import Optional
import sqlalchemy as sa
from sqlalchemy import (
    String, Integer, Boolean, Text, BigInteger, DateTime, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin
from backend.utils.uid import new_id_default

class Banner(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'banners'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String)
    mobile_image_url: Mapped[Optional[str]] = mapped_column(String)
    link_url: Mapped[Optional[str]] = mapped_column(String)
    position: Mapped[str] = mapped_column(String, default="home_main") # e.g., home_main, sidebar, popup
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    device_type: Mapped[str] = mapped_column(String, default="all") # all, desktop, mobile

    __table_args__ = (
        Index("ix_banners_tenant_active_order", "tenant_id", "is_active", "deleted_at", "order_index"),
    )

class Voucher(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'vouchers'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    type: Mapped[str] = mapped_column(String, default="FIXED") # FIXED, PERCENT, SHIPPING
    title: Mapped[Optional[str]] = mapped_column(String)
    subtitle: Mapped[Optional[str]] = mapped_column(String)
    # 💰 BigInteger VNĐ — số tiền giảm (FIXED) hoặc 0-100 (PERCENT, lưu nguyên để tránh float)
    value: Mapped[int] = mapped_column(BigInteger, default=0)
    # 💰 BigInteger VNĐ — ngưỡng đơn tối thiểu để áp mã
    min_spend: Mapped[int] = mapped_column(BigInteger, default=0)
    # 💰 BigInteger VNĐ — giảm tối đa (cho PERCENT voucher)
    max_discount: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[Optional[sa.DateTime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[sa.DateTime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped[str] = mapped_column(String, default="DISCOUNT") # DISCOUNT, SHIPPING, GIFT
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_viral: Mapped[bool] = mapped_column(Boolean, default=False) # Elite V2.2: Explicit Viral Control
    priority: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[Optional[dict[str, object]]] = mapped_column(JSONB, default={})

    __table_args__ = (
        Index("ix_vouchers_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_vouchers_deleted_at", "deleted_at"),
        Index("ix_vouchers_active_viral", "is_active", "is_viral"),
        Index("ix_vouchers_performance_active", "tenant_id", "is_active", "deleted_at", "start_date", "end_date"),
    )

class ComboDeal(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'combo_deals'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    name: Mapped[str] = mapped_column(String) # e.g., "Mua 2 Tặng 1", "Combo Số Lượng"
    type: Mapped[str] = mapped_column(String, default="BUY_X_GET_Y") # BUY_X_GET_Y, BUNDLE_PRICE
    condition_payload: Mapped[Optional[dict[str, object]]] = mapped_column(JSONB) # {"buy_qty": 2, "product_ids": [...]}
    reward_payload: Mapped[Optional[dict[str, object]]] = mapped_column(JSONB) # {"get_qty": 1, "discount_percent": 100}
    start_date: Mapped[Optional[sa.DateTime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[sa.DateTime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
