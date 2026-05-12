"""
ClickFraudEvent — SQLAlchemy 2.0 model
Lưu trữ mọi click event đã được phân tích, phục vụ:
- Dashboard real-time
- Weekly investigation report
- Smart Bidding poison prevention
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.models.base import AuditMixin, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ClickFraudEvent(Base, AuditMixin):
    """
    Bản ghi phân tích một click event từ Google Ads.
    created_at = thời điểm click xảy ra (từ AuditMixin).
    """

    __tablename__ = "click_fraud_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Google Ads tracking ---
    gclid: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ad_group_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    keyword: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # --- Network ---
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    landing_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # --- IP Intelligence ---
    ip_country: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    ip_org: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    is_datacenter: Mapped[bool] = mapped_column(Boolean, default=False)
    is_vpn: Mapped[bool] = mapped_column(Boolean, default=False)
    is_tor: Mapped[bool] = mapped_column(Boolean, default=False)
    is_proxy: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Behavioral signals ---
    session_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    scroll_depth_percent: Mapped[float] = mapped_column(Float, default=0.0)
    mouse_events_count: Mapped[int] = mapped_column(Integer, default=0)
    touch_events_count: Mapped[int] = mapped_column(Integer, default=0)
    webdriver_detected: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Fraud scoring ---
    fraud_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    verdict: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )  # CLEAN | SUSPICIOUS | FRAUD
    triggered_signals: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON list of signal names
    reasoning: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # [V3.0 Agentic] Deep reasoning logs from AI Agent
    session_fingerprint: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # --- Reporting status ---
    reported_to_google: Mapped[bool] = mapped_column(Boolean, default=False)
    investigation_batch_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_cfe_verdict_created", "verdict", "created_at"),
        Index("ix_cfe_ip_created", "ip_address", "created_at"),
        Index("ix_cfe_gclid", "gclid"),
    )


class GoogleAdsCampaignLog(Base, AuditMixin):
    """
    Nhật ký quản lý chiến dịch Google Ads.
    Lưu trữ mọi thay đổi về trạng thái, ngân sách để đối soát.
    """
    __tablename__ = "google_ads_campaign_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    campaign_name: Mapped[str] = mapped_column(String(256), nullable=False)
    
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # CREATE | UPDATE_STATUS | UPDATE_BUDGET
    status_before: Mapped[Optional[str]] = mapped_column(String(32))
    status_after: Mapped[Optional[str]] = mapped_column(String(32))
    
    budget_before_vnd: Mapped[Optional[float]] = mapped_column(Float)
    budget_after_vnd: Mapped[Optional[float]] = mapped_column(Float)
    
    actor_id: Mapped[Optional[int]] = mapped_column(Integer) # ID Admin thực hiện
    note: Mapped[Optional[str]] = mapped_column(Text)
    
    policy_score: Mapped[Optional[float]] = mapped_column(Float)
    is_compliant: Mapped[bool] = mapped_column(Boolean, default=True)

    # Neural Audit v2.6
    seo_score: Mapped[Optional[float]] = mapped_column(Float)
    sge_score: Mapped[Optional[float]] = mapped_column(Float)
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    landing_page_url: Mapped[Optional[str]] = mapped_column(String(512))

    __table_args__ = (
        Index("ix_gacl_campaign_created", "campaign_id", "created_at"),
    )


class IPBlacklist(Base, AuditMixin):
    """
    Danh sách đen các IP bị chặn do nghi ngờ gian lận.
    """
    __tablename__ = "ads_ip_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(45), unique=True, nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(256))
    fraud_score: Mapped[Optional[float]] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Metadata trinh sát
    country: Mapped[Optional[str]] = mapped_column(String(8))
    org: Mapped[Optional[str]] = mapped_column(String(128))


class NegativeKeyword(Base, AuditMixin):
    """
    Danh sách từ khóa phủ định cấp Chiến dịch hoặc Tài khoản.
    """
    __tablename__ = "ads_negative_keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[Optional[str]] = mapped_column(String(64), index=True) # None = Toàn tài khoản
    keyword_text: Mapped[str] = mapped_column(String(256), nullable=False)
    match_type: Mapped[str] = mapped_column(String(16), default="EXACT") # BROAD | PHRASE | EXACT
    
    is_synced: Mapped[bool] = mapped_column(Boolean, default=False) # Đã đồng bộ lên Google Ads chưa
