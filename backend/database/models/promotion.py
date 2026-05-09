from typing import Optional
import sqlalchemy as sa
from sqlalchemy import (
    String, Integer, Boolean, Text, Float, DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin

class Banner(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'banners'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String)
    mobile_image_url: Mapped[Optional[str]] = mapped_column(String)
    link_url: Mapped[Optional[str]] = mapped_column(String)
    position: Mapped[str] = mapped_column(String, default="home_main") # e.g., home_main, sidebar, popup
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    device_type: Mapped[str] = mapped_column(String, default="all") # all, desktop, mobile

class Voucher(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'vouchers'

    id: Mapped[str] = mapped_column(String, primary_key=True) # E.g., SALE30K, SHIP0
    type: Mapped[str] = mapped_column(String, default="FIXED") # FIXED, PERCENT, SHIPPING
    title: Mapped[Optional[str]] = mapped_column(String)
    subtitle: Mapped[Optional[str]] = mapped_column(String)
    value: Mapped[float] = mapped_column(Float, default=0) # amount or percentage
    min_spend: Mapped[float] = mapped_column(Float, default=0)
    max_discount: Mapped[Optional[float]] = mapped_column(Float)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[Optional[sa.DateTime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[sa.DateTime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped[str] = mapped_column(String, default="DISCOUNT") # DISCOUNT, SHIPPING, GIFT
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[Optional[dict[str, object]]] = mapped_column(JSONB, default={})

class ComboDeal(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'combo_deals'

    id: Mapped[str] = mapped_column(String, primary_key=True) # UUID
    name: Mapped[str] = mapped_column(String) # e.g., "Mua 2 Tặng 1", "Combo Số Lượng"
    type: Mapped[str] = mapped_column(String, default="BUY_X_GET_Y") # BUY_X_GET_Y, BUNDLE_PRICE
    condition_payload: Mapped[Optional[dict[str, object]]] = mapped_column(JSONB) # {"buy_qty": 2, "product_ids": [...]}
    reward_payload: Mapped[Optional[dict[str, object]]] = mapped_column(JSONB) # {"get_qty": 1, "discount_percent": 100}
    start_date: Mapped[Optional[sa.DateTime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[sa.DateTime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
