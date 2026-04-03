"""
Support Inbox Schemas — Admin View
===================================
Read-only schemas for the Admin Support Chat History viewer.
Follows Elite V2.2 static typing standards.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class SupportSessionSummary(BaseModel):
    """One row in the sessions list view."""
    session_id: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    product_slug: Optional[str]
    message_count: int
    last_intent: Optional[str]
    last_message_at: Optional[str]  # ISO string


class SupportSessionListResponse(BaseModel):
    data: list[SupportSessionSummary]
    total: int


class SupportChatMessageView(BaseModel):
    """Single decrypted message in a session thread."""
    id: str
    role: str           # "user" | "assistant"
    content: str        # Decrypted plaintext
    intent: Optional[str]
    created_at: Optional[str]


class SupportSessionDetailResponse(BaseModel):
    session_id: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    product_slug: Optional[str]
    messages: list[SupportChatMessageView]
