from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.database.models.base import Base, AuditMixin, TenantMixin
from backend.utils.uid import new_id_default

class SystemOTP(Base, AuditMixin, TenantMixin):
    """
    Elite V2.2: Secure OTP Storage for Login-OTP flow.
    Supports both Phone and Email identifiers.
    """
    __tablename__ = "system_otps"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id_default)
    identifier: Mapped[str] = mapped_column(String, index=True) # email or phone
    code: Mapped[str] = mapped_column(String(10))
    token: Mapped[str] = mapped_column(String(255), index=True) # Reference token for verification
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sys_otp_identifier_token", "identifier", "token"),
    )

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > datetime.now(timezone.utc)
