from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CampaignSchema(BaseModel):
    """Serializes ContentCampaign ORM → JSON response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    source_input: str
    reviewer_type: str = "ADMIN_MANUAL"
    current_step: int = 1
    status: str = "WAITING_FOR_REVIEW"
    category: str = "CREATIVE_CONTENT"

    gold_metadata: Optional[Dict[str, Any]] = None
    topic_data: Optional[Dict[str, Any]] = None
    assets_data: Optional[Union[List[Any], Dict[str, Any]]] = None
    outline_data: Optional[Dict[str, Any]] = None
    draft_content: Optional[str] = None
    search_count: int = 0
    unique_score: float = 1.0
    # final_html is deferred — only present when explicitly loaded
    final_html: Optional[str] = None

    # AuditMixin fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CampaignListResponse(BaseModel):
    """Paginated list of campaigns."""

    model_config = ConfigDict(strict=True)

    items: List[CampaignSchema]
    total: int
    limit: int
    offset: int
