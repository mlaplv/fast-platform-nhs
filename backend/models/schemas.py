from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from enum import Enum
from datetime import datetime

class AgentSignal(str, Enum):
    PROCEED_NEXT = "PROCEED_NEXT"
    REDO_PREVIOUS = "REDO_PREVIOUS"
    FAIL_GRACEFULLY = "FAIL_GRACEFULLY"

class CampaignStep(BaseModel):
    step_number: int
    name: str
    status: str = "PENDING"
    result: Optional[Dict[str, Any]] = None
    agent_msg: Optional[str] = None
    retry_count: int = 0

class ContentCampaign(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    source_input: str
    reviewer_type: str = "ADMIN_MANUAL"
    current_step: int = 1
    status: str = "WAITING_FOR_REVIEW"
    gold_metadata: Optional[Dict[str, Any]] = {}
    topic_data: Optional[Dict[str, Any]] = {}
    assets_data: Optional[List[Any]] = []
    outline_data: Optional[Dict[str, Any]] = {}
    draft_content: Optional[str] = None
    unique_score: float = 0.0
    search_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

class AgentResponse(BaseModel):
    signal: AgentSignal
    data: Any
    message: Optional[str] = None
