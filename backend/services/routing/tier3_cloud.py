import asyncio
import os
import logging
import json
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from litellm import RateLimitError, AuthenticationError, ServiceUnavailableError, Timeout as LiteLLMTimeout

from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.prompts import composer

logger = logging.getLogger("api-gateway")

class Tier3Output(BaseModel):
    """Structured output for Tier 3 Deep Reasoning."""
    model_config = ConfigDict(strict=True)
    message: str = Field(description="The sharp and concise response from XoHi")
    requires_confirmation: bool = Field(default=False, description="Safety gate for database mutations")
    action: IntentAction = Field(default=IntentAction.ANALYZE, description="The primary action type")
    intent_type: str = Field(default="DEEP_ANALYSIS", description="The classified intent category")
    ui_action: str = Field(default="", description="The frontend widget to trigger, if applicable")
    action_data: dict = Field(default_factory=dict, description="Pre-filled data for the frontend form")

SYSTEM_CORE_DIRECTIVE = os.getenv("SYSTEM_CORE_DIRECTIVE", "")

@dataclass
class Tier3Deps:
    """Dependencies for Tier 3 Deep Reasoning (XoHi)."""
    screen_context: Optional[dict[str, object]] = None
    rotator: Optional[object] = None
    base_directive: str = ""
    kb_index: str = ""

class Tier3CloudRouter:
    def __init__(self):
        self.rotator = key_rotator
        
        # [THIẾT QUÂN LUẬT] PydanticAI Agent with Deps
        self.agent = Agent(
            deps_type=Tier3Deps,
            output_type=Tier3Output,
            system_prompt=composer.compose("t3_assistant_premium")
        )

        @self.agent.system_prompt
        def inject_context(ctx: RunContext[Tier3Deps]) -> str:
            parts = [ctx.deps.base_directive]
            if ctx.deps.kb_index:
                parts.append(f"\n[KNOWLEDGE_INDEX]\n{ctx.deps.kb_index}")
            if ctx.deps.screen_context:
                parts.append(f"\n[SCREEN_CONTEXT]\n{json.dumps(ctx.deps.screen_context, ensure_ascii=False)}")
            return "\n".join(parts)

        @self.agent.tool
        async def fetch_topic_knowledge(ctx: RunContext[Tier3Deps], topic_id: str) -> str:
            """
            Lấy kiến thức chi tiết về một chủ đề cụ thể (Layer 2 Topic Fetch).
            Dùng khi sếp hỏi sâu về một mục trong [KNOWLEDGE_INDEX].
            """
            from backend.services.ai_engine.tools.kb_service import kb_service
            return await kb_service.fetch_topic(topic_id)

        @self.agent.tool
        async def fuzzy_search_transcripts(ctx: RunContext[Tier3Deps], query: str) -> str:
            """
            Tìm kiếm dữ liệu thô từ hệ thống kiến thức (Layer 3 Raw Search).
            Dùng khi không tìm thấy thông tin trong [KNOWLEDGE_INDEX] hoặc cần dẫn chứng chi tiết từ bài viết/hóa đơn cũ.
            """
            from backend.services.ai_engine.tools.kb_service import kb_service
            return await kb_service.fuzzy_search_raw(query)

    async def reason(self, transcript: str, context: list[dict[str, object]] | None = None, screen_context: dict[str, object] | None = None) -> IntentResponse:
        """
        C.O.R.E: Deep Reasoning — [THIẾT QUÂN LUẬT] Pro Mode.
        """
        history = []
        if context:
            for msg in context:
                if msg.get("role") != "system":
                    history.append(msg)

        # [TRINITY DISPATCHER] Waterfall logic decoupled
        from backend.services.xohi_memory import xohi_memory
        kb_index = await xohi_memory.get_kb_index()

        deps = Tier3Deps(
            screen_context=screen_context,
            rotator=key_rotator,
            base_directive=SYSTEM_CORE_DIRECTIVE,
            kb_index=kb_index
        )

        try:
            result = await trinity_bridge.run(
                self.agent,
                transcript,
                deps=deps,
                message_history=history
            )
            
            output: Tier3Output = result

            return IntentResponse(
                status="success",
                action=output.action,
                message=output.message,
                router_tier=RouterTier.TIER_3_CLOUD,
                cost_tokens=0.0,
                requires_confirmation=output.requires_confirmation,
                data={
                    "intent_type": output.intent_type,
                    "ui_action": output.widget_id if hasattr(output, 'widget_id') else output.ui_action,
                    **output.action_data
                },
            )
            
        except Exception as e:
            logger.error(f"[T3 Waterfall] Trinity critical failure: {e}")
            return IntentResponse(
                status="error",
                action=IntentAction.ANALYZE,
                message="Hệ thống đang quá tải. Xô Hi sẽ phản hồi sếp sớm nhất có thể.",
                router_tier=RouterTier.TIER_3_CLOUD,
                cost_tokens=0.0,
                data={},
            )

    async def stream_reason(self, transcript: str, context: list[dict[str, object]] | None = None, screen_context: dict[str, object] | None = None):
        """Streaming version of deep reasoning."""
        history = []
        if context:
            for msg in context:
                if msg.get("role") != "system":
                    history.append(msg)

        from backend.services.xohi_memory import xohi_memory
        kb_index = await xohi_memory.get_kb_index()

        deps = Tier3Deps(
            screen_context=screen_context,
            rotator=key_rotator,
            base_directive=SYSTEM_CORE_DIRECTIVE,
            kb_index=kb_index
        )

        try:
            async with trinity_bridge.run_stream(
                self.agent,
                transcript,
                deps=deps,
                message_history=history
            ) as result:
                # [V81.2] Use stream_structured for agents with output_type
                last_len = 0
                try:
                    async for structured, _ in result.stream_structured(debounce_by=None):
                        # Safety: structured could be None or message field could be missing during early frames
                        if not structured: continue
                        msg = getattr(structured, "message", "") or ""
                        if len(msg) > last_len:
                            chunk = msg[last_len:]
                            yield chunk
                            last_len = len(msg)
                except (asyncio.CancelledError, GeneratorExit):
                    logger.debug("[T3 Stream] Loop interrupted by client.")
                    raise # Propagate to exit async with cleanly
                except Exception as e:
                    logger.error(f"[T3 Stream] Inner loop failure: {e}")
                    # Phase 22.2: Do not re-yield here to avoid corrupting stream framing
                    
        except (asyncio.CancelledError, GeneratorExit):
            # Normal exit/cancellation — strictly do not yield or await here
            logger.debug("[T3 Stream] Connection closed by client.")
            return # Exit generator gracefully
        except Exception as e:
            # Check if generator is still valid before yielding
            logger.error(f"[T3 Stream] Critical failure: {e}")
            return
