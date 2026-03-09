from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class IntentAction(str, Enum):
    READ = "READ"
    MUTATE = "MUTATE"
    ANALYZE = "ANALYZE"
    COUNT = "COUNT"
    CONTENT_CREATE = "CONTENT_CREATE"
    CONTENT_APPROVE = "CONTENT_APPROVE"
    CONTENT_REJECT = "CONTENT_REJECT"
    HARDWARE_SLEEP = "HARDWARE_SLEEP"

class RouterTier(str, Enum):
    TIER_1_HEURISTIC = "1"
    TIER_2_SEMANTIC = "2"
    TIER_3_REASONING = "3"

class IntentRequest(BaseModel):
    transcript: str
    user_id: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    screen_context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class IntentResponse(BaseModel):
    status: str = Field(default="success")
    message: str = Field(default="")
    action: IntentAction = Field(default=IntentAction.READ)
    router_tier: RouterTier = Field(default=RouterTier.TIER_2_SEMANTIC)
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    cost_tokens: float = Field(default=0.0)

    class Config:
        strict = True
