from enum import Enum
from typing import Dict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class IntentAction(str, Enum):
    READ = "READ"
    MUTATE = "MUTATE"
    ANALYZE = "ANALYZE"
    COUNT = "COUNT"
    CONTENT_CREATE = "CONTENT_CREATE"
    CONTENT_APPROVE = "CONTENT_APPROVE"
    CONTENT_REJECT = "CONTENT_REJECT"
    HARDWARE_SLEEP = "HARDWARE_SLEEP"
    WAKE_ROUTINE = "WAKE_ROUTINE"

class RouterTier(str, Enum):
    TIER_1_HEURISTIC = "1"
    TIER_2_SEMANTIC = "2"
    TIER_3_REASONING = "3"
    TIER_3_CLOUD = "3"  # Alias for T3 Cloud path (tier3_cloud.py)

class IntentRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    modality: Optional[str] = "voice"
    context: Optional[Dict[str, object]] = Field(default_factory=dict)
    screen_context: Optional[Dict[str, object]] = Field(default_factory=dict)

class IntentResponse(BaseModel):
    status: str = Field(default="success")
    message: str = Field(default="")
    action: IntentAction = Field(default=IntentAction.READ)
    router_tier: RouterTier = Field(default=RouterTier.TIER_2_SEMANTIC)
    data: Optional[Dict[str, object]] = Field(default_factory=dict)

    # Phase 76.4: Explicit VUI & Semantic Context
    semantic_results: Optional[str] = Field(default=None)
    vui_context: Optional[Dict[str, object]] = Field(default_factory=dict)

    cost_tokens: float = Field(default=0.0)
    requires_confirmation: bool = Field(default=False)

    model_config = ConfigDict(strict=False)

class IntentMapUpdate(BaseModel):
    model_config = ConfigDict(strict=True)
    mapping: Dict[str, str]
