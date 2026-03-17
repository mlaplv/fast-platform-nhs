from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Union
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime

class AgentSignal(str, Enum):
    PROCEED_NEXT = "PROCEED_NEXT"
    REDO_PREVIOUS = "REDO_PREVIOUS"
    FAIL_GRACEFULLY = "FAIL_GRACEFULLY"

class CampaignStep(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    step_number: int
    name: str
    status: str = "PENDING"
    result: Optional[Dict[str, object]] = None
    agent_msg: Optional[str] = None
    retry_count: int = 0

class ContentCampaign(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    id: str
    user_id: Optional[str] = None
    source_input: Optional[str] = ""
    reviewer_type: str = "ADMIN_MANUAL"
    current_step: int = 1
    status: str = "WAITING_FOR_REVIEW"
    gold_metadata: Optional[Dict[str, object]] = Field(default_factory=dict)
    topic_data: Optional[Dict[str, object]] = Field(default_factory=dict)
    assets_data: Optional[Union[List[object], Dict[str, object]]] = Field(default_factory=list)
    outline_data: Optional[Dict[str, object]] = Field(default_factory=dict)
    draft_content: Optional[str] = None
    final_html: Optional[str] = None
    search_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

class AgentResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    signal: AgentSignal
    data: Optional[Dict[str, object]] = None
    message: Optional[str] = None

class CampaignListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    id: str
    topic_data: Optional[Dict[str, object]] = None
    status: str
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
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, object]] = None

# Rule R106: Explicit model rebuild for complex type resolution
ContentCampaign.model_rebuild()
AgentResponse.model_rebuild()
GenericResponse.model_rebuild()
