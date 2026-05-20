from __future__ import annotations

from typing import Dict, List, Optional, Union
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

# --- Core Enums ---
class AgentSignal(str, Enum):
    PROCEED_NEXT = "PROCEED_NEXT"
    REDO_PREVIOUS = "REDO_PREVIOUS"
    FAIL_GRACEFULLY = "FAIL_GRACEFULLY"

class CampaignStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ReviewerType(str, Enum):
    ADMIN_MANUAL = "ADMIN_MANUAL"
    AI_AUTO = "AI_AUTO"
    HYBRID = "HYBRID"

# --- Models ---
class CampaignStep(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    step_number: int
    name: str
    status: CampaignStatus = CampaignStatus.PENDING
    result: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = None
    agent_msg: Optional[str] = None
    retry_count: int = 0

class ContentCampaign(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    id: str
    user_id: Optional[str] = None
    source_input: Optional[str] = ""
    reviewer_type: ReviewerType = ReviewerType.ADMIN_MANUAL
    current_step: int = 1
    status: CampaignStatus = CampaignStatus.WAITING_FOR_REVIEW
    gold_metadata: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = Field(default_factory=dict)
    topic_data: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = Field(default_factory=dict)
    assets_data: Optional[Union[List[Union[str, int, float, bool, None, Dict, List]], Dict[str, Union[str, int, float, bool, None, Dict, List]]]] = Field(default_factory=list)
    outline_data: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = Field(default_factory=dict)
    draft_content: Optional[str] = None
    final_html: Optional[str] = None
    search_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    signal: AgentSignal
    data: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = None
    message: Optional[str] = None

class GenericResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = None

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
    analysis_report: Optional[Dict[str, object]] = None
    final_html: Optional[str] = None

    # AuditMixin fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CampaignListItem(BaseModel):
    """Minified campaign item for lists."""
    model_config = ConfigDict(from_attributes=True, strict=True)
    id: str
    topic_data: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = None
    status: CampaignStatus
    current_step: int
    created_at: datetime
    user_id: Optional[str] = None
    category: Optional[str] = None

class CampaignListResponse(BaseModel):
    """Paginated list of campaigns."""
    model_config = ConfigDict(from_attributes=True, strict=True)
    items: List[CampaignListItem]
    total: int
    has_more: bool
    limit: int
    offset: int

class ContentCleanOptions(BaseModel):
    model_config = ConfigDict(strict=False)
    stripFont: bool = True
    stripAlign: bool = True
    stripRedundantWrappers: bool = True
    stripEmpty: bool = True
    deduplicateContent: bool = True

class ContentCleanRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str
    options: Optional[ContentCleanOptions] = None

class AdhocAnalysisRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: Optional[str] = None
    topic: Optional[str] = None
    content_type: Optional[str] = None
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
    model_config = ConfigDict(strict=True)
    content: str
    target_snippet: str
    annotation_type: str
    error_message: str
    topic: Optional[str] = None

class SurgeonBoostRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str
    topic: str = ""
    campaign_id: Optional[str] = None

class NeuralRewriteRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str
    topic: str = ""
    feedback: str = ""
    content_type: Optional[str] = "article"
    metadata: Optional[Dict[str, object]] = None
    user_note: Optional[str] = None

# Rule R106: Explicit model rebuild for complex type resolution
ContentCampaign.model_rebuild()
AgentResponse.model_rebuild()
GenericResponse.model_rebuild()
