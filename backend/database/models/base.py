from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, String, Index
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()

def utcnow():
    return datetime.now(timezone.utc)

class AuditMixin:
    """Standardized audit fields for transparency."""
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class SoftDeleteMixin:
    """Standardized soft delete logic (Rule R38)."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class TenantMixin:
    """Standardized multi-tenancy support."""
    tenant_id: Mapped[str] = mapped_column(String, default="default", index=True)
