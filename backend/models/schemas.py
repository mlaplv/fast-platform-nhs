from pydantic import BaseModel, Field
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
    id: UUID = Field(default_factory=uuid4)
    name: str
    current_step: int = 1
    status: str = "RUNNING"
    steps: List[CampaignStep] = []
    gold_metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)

class AgentResponse(BaseModel):
    signal: AgentSignal
    data: Any
    message: Optional[str] = None
