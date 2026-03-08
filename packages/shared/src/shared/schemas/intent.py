from pydantic import BaseModel, ConfigDict, Field
from enum import Enum
from typing import Optional, Dict

class IntentAction(str, Enum):
    # Rule R5: "Số lượng", "Trạng thái", "Đếm" -> GET/COUNT
    COUNT = "COUNT"
    READ = "READ"
    MUTATE = "MUTATE" # Chuyển cho Draft mutation (R11)
    ANALYZE = "ANALYZE" # Chuyển cho AI phân tích sâu
    CONTENT_CREATE = "CONTENT_CREATE" # V62.1: Content Factory — Sáng tạo nội dung SEO
    CONTENT_APPROVE = "CONTENT_APPROVE" # V62.1: Duyệt bước bài viết
    CONTENT_REJECT = "CONTENT_REJECT" # V62.1: Từ chối / Yêu cầu sửa lại


class RouterTier(int, Enum):
    """Phễu Lọc 3 Tầng - Router Tier indicator"""
    TIER_1_HEURISTIC = 1   # Regex/Keyword → 0 token, <10ms
    TIER_2_SEMANTIC = 2    # Cloud Flash (Gemini Flash) → fast extraction
    TIER_3_CLOUD = 3       # Cloud LLM fallback (Dify/Claude/Gemini)

class IntentRequest(BaseModel):
    query: str = Field(..., max_length=2000)  # HELLFIRE: Matches SemanticShield MAX_INPUT_LENGTH
    action_type: Optional[IntentAction] = None
    target: Optional[str] = Field(None, max_length=100)
    session_id: Optional[str] = Field(None, max_length=64)
    modality: Optional[str] = "text" # "text" or "voice"
    screen_context: Optional[Dict[str, object]] = None  # UI context for deictic resolution

class IntentResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    status: str
    action: IntentAction
    data: Optional[Dict[str, object]] = None  # HELLFIRE: R25 — was Any
    message: str
    router_tier: Optional[int] = None      # Which tier resolved (1, 2, 3)
    cost_tokens: float = 0.0               # Token cost for telemetry (R19)
    requires_confirmation: bool = False     # V21.0: Safety gate for MUTATE actions

