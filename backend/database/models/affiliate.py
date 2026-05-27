"""
Elite V2.2: Affiliate / CTV (Cộng Tác Viên) Data Models
Viral 2026 — Multi-tier commission with AES-GCM integrity seals
"""
from typing import Optional, List
import uuid
import sqlalchemy as sa
from sqlalchemy import String, Float, Integer, Boolean, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base, AuditMixin, SoftDeleteMixin, TenantMixin


class CommissionTier(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    """
    Viral 2026: Commission Tier Configuration.
    Admin-managed via API — no hardcoded rates.
    """
    __tablename__ = "commission_tiers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100))                      # VD: "Đồng", "Bạc", "Vàng", "Kim Cương"
    min_revenue_threshold: Mapped[float] = mapped_column(Float, default=0.0)  # Mốc doanh số tích lũy để đạt tier
    commission_rate: Mapped[float] = mapped_column(Float, default=0.15)       # 0.15 = 15%
    bonus_rate: Mapped[float] = mapped_column(Float, default=0.0)             # Bonus % thêm khi vượt mốc tháng
    max_withdrawal_per_month: Mapped[float] = mapped_column(Float, default=50_000_000.0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # Tier mặc định khi đăng ký

    affiliates: Mapped[List["AffiliateProfile"]] = relationship("AffiliateProfile", back_populates="tier")

    __table_args__ = (
        Index("ix_commission_tiers_tenant_deleted", "tenant_id", "deleted_at"),
    )


class AffiliateProfile(Base, AuditMixin, SoftDeleteMixin, TenantMixin):
    """
    Elite V2.2: CTV (Cộng Tác Viên) Profile.
    1:1 với User. AES-GCM seal bảo vệ balance integrity.
    """
    __tablename__ = "affiliate_profiles"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    ctv_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)   # VD: "MINHTU01"
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", index=True)  # PENDING|ACTIVE|SUSPENDED|BANNED

    # Commission Config
    commission_tier_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("commission_tiers.id"), nullable=True)
    tier: Mapped[Optional["CommissionTier"]] = relationship("CommissionTier", back_populates="affiliates")

    # Aggregated Stats (pre-computed để tránh N+1 trên dashboard)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)           # Tổng GMV
    total_commission: Mapped[float] = mapped_column(Float, default=0.0)        # Tổng hoa hồng earned
    paid_commission: Mapped[float] = mapped_column(Float, default=0.0)         # Đã thanh toán
    total_orders: Mapped[int] = mapped_column(Integer, default=0)              # Số đơn thành công

    # Security V2.2: AES-GCM Integrity Seal (clone LoyaltyService pattern)
    balance_seal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Anti-fraud: Referral chain depth control
    referral_chain_depth: Mapped[int] = mapped_column(Integer, default=0)
    referred_by_ctv_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("affiliate_profiles.id"), nullable=True
    )

    # Encrypted bank info (AES-GCM) — never stored raw
    bank_info_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # type: ignore[name-defined]
    commissions: Mapped[List["CommissionLedger"]] = relationship("CommissionLedger", back_populates="affiliate")
    withdrawals: Mapped[List["WithdrawalRequest"]] = relationship("WithdrawalRequest", back_populates="affiliate")

    __table_args__ = (
        Index("ix_affiliate_profiles_tenant_deleted", "tenant_id", "deleted_at"),
        Index("ix_affiliate_profiles_status", "status", "tenant_id"),
    )


class CommissionLedger(Base, AuditMixin, TenantMixin):
    """
    Elite V2.2: Immutable Commission Ledger.
    Mỗi record = 1 hoa hồng từ 1 đơn hàng. Không soft-delete.
    AES-GCM seal chống tamper DB trực tiếp.
    """
    __tablename__ = "commission_ledger"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    affiliate_id: Mapped[str] = mapped_column(String, ForeignKey("affiliate_profiles.id"), index=True)
    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.id"), unique=True, index=True)  # UNIQUE: idempotency

    # Financial Data (immutable sau khi ghi)
    order_amount: Mapped[float] = mapped_column(Float)
    commission_amount: Mapped[float] = mapped_column(Float)
    rate_applied: Mapped[float] = mapped_column(Float)                  # % tại thời điểm credit
    tier_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Tier name + rate tại thời điểm

    # Lifecycle
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)  # PENDING|CONFIRMED|PAID|CANCELLED|DISPUTED
    confirmed_at: Mapped[Optional[sa.DateTime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    paid_at: Mapped[Optional[sa.DateTime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Security: AES-GCM integrity token
    integrity_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    affiliate: Mapped["AffiliateProfile"] = relationship("AffiliateProfile", back_populates="commissions")

    __table_args__ = (
        Index("ix_commission_ledger_tenant_status", "tenant_id", "status"),
        Index("ix_commission_ledger_affiliate_created", "affiliate_id", "created_at"),
    )


class WithdrawalRequest(Base, AuditMixin, TenantMixin):
    """
    Elite V2.2: CTV Withdrawal Request.
    Bank info được snapshot + encrypt tại thời điểm request.
    Admin approve → ghi paid_at.
    """
    __tablename__ = "withdrawal_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    affiliate_id: Mapped[str] = mapped_column(String, ForeignKey("affiliate_profiles.id"), index=True)

    # Financial
    amount_requested: Mapped[float] = mapped_column(Float)
    amount_approved: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Security: Snapshot bank info lúc request (immutable, encrypted)
    bank_snapshot_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)  # PENDING|APPROVED|REJECTED|PAID
    requested_at: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.func.now())
    processed_at: Mapped[Optional[sa.DateTime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    admin_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Security seal
    integrity_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    affiliate: Mapped["AffiliateProfile"] = relationship("AffiliateProfile", back_populates="withdrawals")

    __table_args__ = (
        Index("ix_withdrawal_requests_tenant_status", "tenant_id", "status"),
    )
