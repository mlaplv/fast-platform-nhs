from typing import Optional
import sqlalchemy as sa
from sqlalchemy import (
    String, Integer, Boolean, Text
)
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin

class Banner(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    __tablename__ = 'banners'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String)
    link_url: Mapped[Optional[str]] = mapped_column(String)
    position: Mapped[str] = mapped_column(String, default="home_main") # e.g., home_main, sidebar, popup
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    device_type: Mapped[str] = mapped_column(String, default="all") # all, desktop, mobile
