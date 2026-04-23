from __future__ import annotations

from typing import Dict, List, Optional, Union
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

    gold_metadata: Optional[Dict[str, object]] = None
    topic_data: Optional[Dict[str, object]] = None
    assets_data: Optional[Union[List[object], Dict[str, object]]] = None
    outline_data: Optional[Dict[str, object]] = None
    draft_content: Optional[str] = None
    search_count: int = 0
    unique_score: float = 1.0
    # final_html is deferred — only present when explicitly loaded
    final_html: Optional[str] = None

    # AuditMixin fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CampaignListItem(BaseModel):
    """Minified campaign item for lists."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    topic_data: Optional[Dict[str, object]] = None
    status: str
    current_step: int
    created_at: Optional[datetime] = None
    user_id: Optional[str] = None

class CampaignListResponse(BaseModel):
    """Paginated list of campaigns."""
    model_config = ConfigDict(strict=True)
    items: List[CampaignListItem]
    total: int
    limit: int
    offset: int
    has_more: bool

class ContentCleanRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str

class AdhocAnalysisRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: Optional[str] = None
    topic: Optional[str] = None
    force: bool = False

class BulkFixRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str
    category: str
    annotations: List[Dict[str, object]] = []

class ScoutTopicRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    topic: str
    campaign_id: Optional[str] = None

class AdhocAutoFixRequest(BaseModel):
    """Ad-hoc auto-fix: sửa từng annotation không cần campaign_id."""
    model_config = ConfigDict(strict=True)
    content: str
    target_snippet: str
    annotation_type: str
    error_message: str
    topic: Optional[str] = None
