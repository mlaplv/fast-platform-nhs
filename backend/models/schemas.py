from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Union
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime, timezone

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

class CampaignListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    id: str
    topic_data: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = None
    status: CampaignStatus
    current_step: int
    created_at: datetime
    user_id: Optional[str] = None
    category: Optional[str] = None

class CampaignListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    items: List[CampaignListItem]
    total: int
    has_more: bool
    limit: int
    offset: int

class GenericResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str # keeping as str for general status labels, but using specific types for data
    message: Optional[str] = None
    data: Optional[Dict[str, Union[str, int, float, bool, None, Dict, List]]] = None

# Rule R106: Explicit model rebuild for complex type resolution
ContentCampaign.model_rebuild()
AgentResponse.model_rebuild()
GenericResponse.model_rebuild()
