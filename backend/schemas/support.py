"""
Support Agent Schemas — SUPPORT_NAME_CLIENT
=============================================
Pydantic V2 schemas for the client-facing support chat endpoint.
All models use strict mode and explicit types (CẤM 'any').
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SupportProductInfo(BaseModel):
    """Metadata for product-related chat responses (Elite V2.2)"""
    id: str = Field(..., description="Product UUID")
    name: str = Field(..., description="Product display name")
    price: float = Field(..., description="Current price")
    price_display: str = Field(..., description="Formatted price string")
    slug: str = Field(..., description="Product URL slug")

    model_config = ConfigDict(frozen=True)


class SupportIntent(str, Enum):
    """Classified intent categories for the support operative."""
    PRODUCT_QUERY  = "PRODUCT_QUERY"
    PRICE_QUERY    = "PRICE_QUERY"
    POLICY_QUERY   = "POLICY_QUERY"
    ORDER_STATUS   = "ORDER_STATUS"
    GENERAL_ADVICE = "GENERAL_ADVICE"
    ESCALATE       = "ESCALATE"
    UNKNOWN        = "UNKNOWN"


class SupportRequest(BaseModel):
    """Inbound chat message from the client (Zero-Auth)."""
    model_config = ConfigDict(strict=True)

    message: str = Field(..., min_length=1, max_length=2000, description="User question")
    session_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Guest session UUID for rate limiting. Generated client-side."
    )
    product_slug: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Optional: slug of the product being viewed. Used for RAG context."
    )
    customer_name: Optional[str] = Field(default="Khách ẩn danh", max_length=100)
    customer_phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, v: str) -> str:
        return v.strip()

    @field_validator("session_id", mode="before")
    @classmethod
    def sanitize_session(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        # Only allow alphanumeric + hyphens (UUID format)
        return s if s.replace("-", "").isalnum() and len(s) <= 64 else None


class SupportResponse(BaseModel):
    """Outbound response from the support operative."""
    model_config = ConfigDict(strict=True)

    ok: bool = True
    reply: str = Field(..., description="AI-generated reply, sanitized and bounded.")
    intent: SupportIntent = Field(default=SupportIntent.UNKNOWN)
    session_id: Optional[str] = Field(default=None)
    product_info: Optional[Dict[str, object]] = Field(default=None, description="Metadata for UI components (ordering, etc.)")
