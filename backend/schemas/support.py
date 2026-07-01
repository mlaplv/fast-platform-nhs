"""
Support Agent Schemas — SUPPORT_NAME_CLIENT
=============================================
Pydantic V2 schemas for the client-facing support chat endpoint.
All models use strict mode and explicit types (CẤM 'any').
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator, JsonValue
from typing import Optional, Dict, List, Union
from backend.schemas.pricing import PricingBreakdown

# Type Aliases for 100% Static Typing (Elite V2.2 Standard)
# Using Pydantic built-in JsonValue for strict compliance (CẤM 'Any')
JSONValue = JsonValue


class SupportProductInfo(BaseModel):
    """Metadata for product-related chat responses (Elite V2.2)"""
    id: str = Field(..., description="Product UUID")
    name: str = Field(..., description="Product display name")
    price: float = Field(..., description="Current price")
    price_display: str = Field(..., description="Formatted price string")
    slug: str = Field(..., description="Product URL slug")
    image_url: Optional[str] = Field(default=None, description="Product main image URL")
    stock: Optional[int] = Field(default=0, description="Real-time stock level for FOMO")

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
    INFO_INGREDIENTS = "INFO_INGREDIENTS"
    INFO_ADDRESS     = "INFO_ADDRESS"
    INFO_HOTLINE     = "INFO_HOTLINE"
    PRICE_QUERY      = "PRICE_QUERY"
    INFO_SHIPPING    = "INFO_SHIPPING"


# SupportPricingContext removed in favor of unified PricingBreakdown (Elite V5.0)


class SupportRequest(BaseModel):
    """Inbound chat message from the client (Zero-Auth)."""
    model_config = ConfigDict(strict=False)

    message: str = Field(..., min_length=1, max_length=2000, description="User question (max 2000 chars to support system prompts from quick actions)")
    session_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Guest session UUID for rate limiting. Generated client-side."
    )
    product_slug: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional: slug of the product being viewed. Used for RAG context."
    )
    customer_name: Optional[str] = Field(default="Khách ẩn danh", max_length=255)
    customer_phone: Optional[str] = Field(default=None, max_length=100)
    user_id: Optional[str] = Field(default=None, max_length=128)
    cart_items: Optional[List[Dict[str, JSONValue]]] = Field(default=None, description="Current cart snapshot from client localStorage.")
    selected_vouchers: Optional[List[str]] = Field(default=None, description="Active voucher IDs from client cart.")
    pricing_context: Optional[PricingBreakdown] = Field(default=None, description="Calculated breakdown from frontend (Ground Truth).")
    cart_epoch: Optional[int] = Field(default=None, description="Current cart epoch on the client to prevent race conditions")
    is_agent: bool = Field(default=False, description="Whether this request is made by a verified external AI Agent")
    a2a_context: Optional[dict[str, object]] = Field(default=None, description="A2A Agent-to-Agent parsed context map")



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

    @field_validator("cart_items", mode="before")
    @classmethod
    def cap_cart_items(cls, v: object) -> object:
        """H-1 Security: Guard against OOM DoS via oversized cart_items payload.
        Max 50 items — any excess is silently truncated at the gate."""
        if isinstance(v, list) and len(v) > 50:
            return v[:50]
        return v

    @field_validator("selected_vouchers", mode="before")
    @classmethod
    def cap_selected_vouchers(cls, v: object) -> object:
        """Cap voucher list to prevent abuse."""
        if isinstance(v, list) and len(v) > 10:
            return v[:10]
        return v


class UrgentSupportRequest(BaseModel):
    """Viral 30-Second Rule: Urgent support request (Zero-Auth)."""
    model_config = ConfigDict(strict=True)
    phone: str = Field(..., min_length=10, max_length=15, description="Client phone number")
    source_url: Optional[str] = Field(default=None, max_length=255, description="URL where the panic button was clicked")


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
    
    # 🎭 Elite V2.2: Rich UI & Active Reasoning
    ui_metadata: Optional[Dict[str, JsonValue]] = Field(default=None, description="Metadata for UI components (cards, buttons, etc.)")
    metadata: Optional[Dict[str, JsonValue]] = Field(default=None, description="Extra metadata like 'think' reasoning snapshots")
    processed_order_id: Optional[str] = Field(default=None, description="UUID of the order processed in this turn")


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
    is_revoked: bool = False
    customer_phone: Optional[str] = None


# ══════════════════════════════════════════════════════════════
# ADMIN KNOWLEDGE MANAGEMENT SCHEMAS
# ══════════════════════════════════════════════════════════════

class SupportKnowledgeBase(BaseModel):
    category: SupportKnowledgeCategory = Field(default=SupportKnowledgeCategory.GENERAL)
    question: str = Field(..., min_length=1)
    answer: str = Field(default="[Đang phân tích dữ liệu...]")
    is_active: bool = True
    priority: int = 0
    tags: Optional[Union[List[str], Dict[str, JSONValue]]] = None
    product_id: Optional[str] = None
    source_type: str = Field(default="TEXT")
    source_url: Optional[str] = None

class CreateSupportKnowledgeRequest(SupportKnowledgeBase):
    pass

class UpdateSupportKnowledgeRequest(BaseModel):
    category: Optional[SupportKnowledgeCategory] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    tags: Optional[Union[List[str], Dict[str, JSONValue]]] = None
    product_id: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None

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


# 🚀 Elite V2.2: Advanced Admin Support Operational Schemas
# (100% Static Typing Compliance - CẤM TUYỆT ĐỐI 'any')

class ExtractContentRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    source_type: str = Field(..., description="Nguồn trích xuất: URL | PDF | HTML")
    source_url: str = Field(..., description="Đường dẫn URL hoặc file tài liệu")

class ExtractContentResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    ok: bool
    text: Optional[str] = None
    error: Optional[str] = None

class OptimizeContentRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    text: str = Field(..., min_length=1, description="Văn bản gốc cần tối ưu")

class OptimizeContentResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    ok: bool
    text: Optional[str] = None
    error: Optional[str] = None

class CheckDuplicateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    text: str = Field(..., min_length=1, description="Văn bản cần kiểm tra trùng lặp")
    current_id: Optional[str] = Field(default=None, description="UUID của item hiện tại (nếu đang sửa)")
    threshold: Optional[float] = Field(default=0.82, ge=0.0, le=1.0, description="Ngưỡng so khớp tương đồng vector")

class DuplicateItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    question: str
    match_score: float
    snippet: str

class CheckDuplicateResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    ok: bool
    has_duplicate: bool = False
    duplicates: list[DuplicateItem] = Field(default_factory=list)
    error: Optional[str] = None
