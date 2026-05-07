"""
Viral Share Schemas — Elite V2026
Strict Pydantic V2 models for share-intent and verify-share endpoints.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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
    """Response after successful verification"""
    valid: bool
    voucher_code: str
    voucher_label: str
    voucher_value: float
    voucher_type: str
    min_spend: float
