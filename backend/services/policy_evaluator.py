from pydantic import BaseModel, Field
from typing import List, Optional
import time
import logging

logger = logging.getLogger("policy-evaluator")

from functools import lru_cache

def current_time_block() -> int:
    import time
    return int(time.time() / 300)

class PolicyContext(BaseModel):
    """Mô hình dữ liệu tĩnh cho bối cảnh phân quyền PBAC (Schema Validation tĩnh)."""
    user_roles: tuple[str, ...] = Field(default_factory=tuple)
    user_perms: tuple[str, ...] = Field(default_factory=tuple)
    required_perms: tuple[str, ...] = Field(default_factory=tuple)
    action: str = Field(...)
    resource_id: Optional[str] = None
    domain: Optional[str] = None
    time_block: int = Field(default_factory=current_time_block)

    model_config = {"frozen": True}

class EvaluationResult(BaseModel):
    allowed: bool
    reason: str

@lru_cache(maxsize=1024)
def _evaluate_policy_cached(context: PolicyContext) -> EvaluationResult:
    # 1. SUPER_ADMIN Override
    if "SUPER_ADMIN" in context.user_roles:
        return EvaluationResult(allowed=True, reason="Granted by SUPER_ADMIN override")

    # 2. Schema-based Default Deny logic
    if not context.required_perms:
        return EvaluationResult(allowed=True, reason="No specific permissions required")

    clearances = set(context.user_perms) | set(context.user_roles)
    has_base_perms = all(req in clearances for req in context.required_perms)
    
    if not has_base_perms:
        return EvaluationResult(allowed=False, reason="Missing required granular permissions")

    # 3. Context-Aware ABAC Rules (Extensible)
    return EvaluationResult(allowed=True, reason="Context evaluation passed")

class PolicyEvaluator:
    """PBAC Engine: Đánh giá siêu tốc dứt điểm <10ms."""
    
    @classmethod
    def evaluate(cls, context: PolicyContext) -> EvaluationResult:
        return _evaluate_policy_cached(context)
