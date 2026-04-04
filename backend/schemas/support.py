"""
Support Agent Schemas — SUPPORT_NAME_CLIENT
=============================================
Pydantic V2 schemas for the client-facing support chat endpoint.
All models use strict mode and explicit types (CẤM 'any').
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Dict
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
    PURCHASE       = "PURCHASE"
    GENERAL_ADVICE = "GENERAL_ADVICE"
    ESCALATE       = "ESCALATE"
    UNKNOWN        = "UNKNOWN"


class SupportKnowledgeCategory(str, Enum):
    """Enum for knowledge base categorization (Elite V2.2)"""
    GENERAL  = "GENERAL"
    POLICY   = "POLICY"
    SHIPPING = "SHIPPING"
    PRODUCT  = "PRODUCT"
    PROMO    = "PROMO"


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
    product_info: Optional[SupportProductInfo] = Field(default=None, description="Metadata for UI components (ordering, etc.)")
    
    # 🚀 Elite V2.2: Async Task Tracking
    status: str = Field(default="DONE", description="State: DONE | PROCESSING | FAILED")
    task_id: Optional[str] = Field(default=None, description="Arq Task UUID for frontend tracking")


class SupportStatusResponse(BaseModel):
    """Outbound status response for Helen AI."""
    model_config = ConfigDict(strict=True)
    helen_enabled: bool
    offline_message: str


class SupportHistoryItem(BaseModel):
    """Individual chat history record (GCM Encrypted or Plaintext)."""
    model_config = ConfigDict(strict=True)
    id: str
    role: str # user | assistant
    content: str # Decrypted text
    intent: Optional[str] = None
    timestamp: Optional[str] = None


# ══════════════════════════════════════════════════════════════
# ADMIN KNOWLEDGE MANAGEMENT SCHEMAS
# ══════════════════════════════════════════════════════════════

class SupportKnowledgeBase(BaseModel):
    category: SupportKnowledgeCategory = Field(default=SupportKnowledgeCategory.GENERAL)
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    is_active: bool = True
    priority: int = 0
    tags: Optional[list[str]] = None

class CreateSupportKnowledgeRequest(SupportKnowledgeBase):
    pass

class UpdateSupportKnowledgeRequest(BaseModel):
    category: Optional[SupportKnowledgeCategory] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    tags: Optional[list[str]] = None

class SupportKnowledgeResponse(SupportKnowledgeBase):
    id: str
    created_at: str # ISO string

class SupportKnowledgeListResponse(BaseModel):
    data: list[SupportKnowledgeResponse]
    total: int

class BulkDeleteRequest(BaseModel):
    ids: list[str]

class BulkToggleRequest(BaseModel):
    ids: list[str]
    is_active: bool
