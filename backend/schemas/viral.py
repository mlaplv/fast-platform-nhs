"""
Viral Share Schemas — Elite V2026
Strict Pydantic V2 models for share-intent and verify-share endpoints.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class VoucherType(str, Enum):
    """Elite V2.2: Standardized voucher types"""
    FIXED = "FIXED"
    PERCENT = "PERCENT"
    SHIPPING = "SHIPPING"


class ViralStatsResponse(BaseModel):
    """Viral FOMO metrics for a product (Elite V2026)"""
    model_config = ConfigDict(frozen=True)

    product_id: str = Field(..., description="Target product UUID")
    share_count: int = Field(0, description="Total organic shares")
    redemption_count: int = Field(0, description="Total successful voucher claims")
    fomo_label: str = Field(..., description="Humanized string (e.g., '499+ đã nhận')")


class ShareIntentRequest(BaseModel):
    """Body for POST /api/v1/client/viral/share-intent"""
    product_id: str = Field(..., min_length=1, max_length=64, description="Product UUID or slug")


class ShareIntentResponse(BaseModel):
    """Successful token issuance response"""
    token: str = Field(..., description="HMAC-SHA256 One-Time Token")
    fingerprint: str = Field(..., description="Device fingerprint (opaque)")
    expires_at: int = Field(..., description="Unix timestamp (UTC) — token expires at")


class VerifyShareRequest(BaseModel):
    """Body for POST /api/v1/client/viral/verify-share"""
    product_id: str = Field(..., min_length=1, max_length=64)
    fingerprint: str = Field(..., min_length=64, max_length=64, description="Device fingerprint from share-intent")
    token: str = Field(..., min_length=64, max_length=64, description="HMAC token from share-intent")
    voucher_id: str = Field(..., min_length=1, max_length=64, description="Voucher code configured in product metadata")

    @field_validator("fingerprint", "token")
    @classmethod
    def must_be_hex(cls, v: str) -> str:
        """Ensure fingerprint and token are valid hex strings (prevents injection)."""
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Must be a valid hex string")
        return v.lower()


class VerifyShareResponse(BaseModel):
    """Response after successful verification — Elite V2026 Enhanced"""
    model_config = ConfigDict(frozen=True)

    valid: bool = Field(..., description="Verification status")
    voucher_code: str = Field(..., description="The code to apply at checkout")
    voucher_label: str = Field(..., description="Main title (e.g. 'Giảm 50K')")
    voucher_subtitle: Optional[str] = Field(None, description="Secondary label (e.g. 'Đơn từ 200K')")
    voucher_value: float = Field(..., description="Numeric discount value")
    voucher_type: VoucherType = Field(..., description="Fixed or Percent")
    min_spend: float = Field(0.0, description="Min order value to use")
    expires_at: Optional[int] = Field(None, description="Voucher expiry timestamp")


class ViralSharePromotion(BaseModel):
    """Configuration for 'share_promotion' in product metadata"""
    enabled: bool = Field(False)
    voucher_id: Optional[str] = Field(None)
    reward_value_label: str = Field("50K", description="Display value (e.g. '50K')")


class ViralSuiteConfig(BaseModel):
    """Full 'viral_suite' object in product metadata"""
    share_promotion: ViralSharePromotion
    share_count: int = Field(0)
    redemption_count: int = Field(0)
