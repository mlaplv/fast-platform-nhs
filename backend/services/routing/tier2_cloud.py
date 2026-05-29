import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from litellm import RateLimitError, AuthenticationError, ServiceUnavailableError, Timeout as LiteLLMTimeout

from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.prompts import composer

logger = logging.getLogger("api-gateway")

class Tier2Output(BaseModel):
    """Structured output for Tier 2 Dispatcher extraction."""
    model_config = ConfigDict(strict=True)
    intent_type: Literal["UI_NAV", "DATA_QUERY", "DEEP_ANALYSIS", "CONTENT_CREATE", "CONTENT_APPROVE", "CONTENT_REJECT", "LEARN_COMMAND", "UNKNOWN"] = Field(
        description="Type of user intent classification"
    )
    target: Literal["order", "revenue", "product", "user", "category", "news", "campaign", "none"] = Field(
        description="The primary entity being targeted"
    )
    timeframe: Literal["today", "this_week", "this_month", "none"] = Field(
        description="Temporal scope of the request"
    )
    widget_id: str = Field(
        description="The specific frontend widget to trigger"
    )
    status: Literal["pending", "processing", "completed", "none"] = Field(
        description="Entity status filtering"
    )
    learn_keyword: Optional[str] = Field(None, description="Từ khóa sếp muốn dạy")
    learn_target: Optional[str] = Field(None, description="Tính năng hoặc Widget sếp muốn gán cho từ khóa")

# R1.6: Cache schema at Global Scope — CẤM tạo lại mỗi request
TIER2_SCHEMA = Tier2Output.model_json_schema()

INTENT_TO_ACTION_MAP = {
    "UI_NAV": IntentAction.READ,
    "DATA_QUERY": IntentAction.COUNT,
    "DEEP_ANALYSIS": IntentAction.ANALYZE,
    "CONTENT_CREATE": IntentAction.CONTENT_CREATE,
    "CONTENT_APPROVE": IntentAction.CONTENT_APPROVE,
    "CONTENT_REJECT": IntentAction.CONTENT_REJECT,
    "LEARN_COMMAND": IntentAction.MUTATE,
    "UNKNOWN": IntentAction.READ
}

@dataclass
class Tier2Deps:
    """Dependencies for Tier 2 Dispatcher."""
    screen_context: Optional[dict] = None
    rotator: Optional[object] = None
    kb_index: str = ""

class Tier2CloudRouter:
    def __init__(self):
        # R1.4: TrinityBridge handles models from DB/Chain.
        self.rotator = key_rotator
        
        # PydanticAI Agent Initialization
        self.agent = Agent(
            deps_type=Tier2Deps,
            output_type=Tier2Output,
            system_prompt=composer.compose("t2_dispatcher_premium")
        )

        @self.agent.system_prompt
        def add_context(ctx: RunContext[Tier2Deps]) -> str:
            parts = []
            if ctx.deps.kb_index:
                parts.append(f"\n[KNOWLEDGE_INDEX]\n{ctx.deps.kb_index}")
            if ctx.deps.screen_context:
                parts.append(f"\n[SCREEN_CONTEXT]\n{json.dumps(ctx.deps.screen_context, ensure_ascii=False)}")
            return "\n".join(parts)

    async def extract(self, transcript: str, context: list = None, screen_context: dict | None = None) -> Optional[IntentResponse]:
        # R1.8: Anti-Blocking — Truncate transcript to protect event loop
        transcript = transcript[:500]

        # Clean up context for PydanticAI
        history = []
        if context:
            for msg in context:
                if msg.get("role") != "system":
                    history.append(msg)
        
        # [TRINITY DISPATCHER] Waterfall logic decoupled
        from backend.services.xohi_memory import xohi_memory
        kb_index = await xohi_memory.get_kb_index()

        deps = Tier2Deps(screen_context=screen_context, rotator=key_rotator, kb_index=kb_index)

        try:
            result = await trinity_bridge.run(
                self.agent, 
                transcript, 
                deps=deps, 
                message_history=history
            )
            
            output: Tier2Output = result
            action = INTENT_TO_ACTION_MAP.get(output.intent_type, IntentAction.READ)

            return IntentResponse(
                status="success", 
                action=action, 
                message="", 
                router_tier=RouterTier.TIER_2_SEMANTIC, 
                cost_tokens=0.0, 
                data={
                    "intent_type": output.intent_type, 
                    "ui_action": output.widget_id, 
                    "target": output.target, 
                    "timeframe": output.timeframe, 
                    "widget_id": output.widget_id, 
                    "status": output.status,
                    "learn_keyword": output.learn_keyword,
                    "learn_target": output.learn_target,
                    **({"category": "SESSION_CTRL", "action": "HARDWARE_SLEEP"} if output.intent_type == "UI_NAV" else {})
                }
            )
        except Exception as e:
            logger.error(f"[T2 Dispatcher] Trinity failure: {e}")
            return None
