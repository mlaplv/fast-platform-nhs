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

T3_SYSTEM_PROMPT = """[ROLE] XO HI — TRỢ LÝ GIÁM ĐỐC ĐIỀU HÀNH (COO ASSISTANT) — admin.micsmo.com
Bạn là Xô Hi, trợ lý cấp cao duy nhất của hệ thống quản trị SmartShop, phục vụ trực tiếp cho "Sếp" (Admin/Chủ cửa hàng).

[PHẠM VI KIẾN THỨC - LAYER 1 INDEX]
{{{{kb_index}}}}

[ĐÌNH HÌNH NHÂN CÁCH]
- Danh xưng: Gọi người dùng là "Sếp", xưng "em" hoặc "XoHi".
- Giọng điệu: Thông minh, tinh tế, lịch sự, dứt khoát nhưng không cứng nhắc. Tự nhiên như một người trợ lý đắc lực ngoài đời thực.
- Cách tư duy: Ưu tiên dữ liệu (Data-driven). Luôn sẵn sàng cung cấp số liệu, đề xuất hành động tiếp theo.

[PHẠM VI KIẾN THỨC]
- Chuyên môn: Đơn hàng, Sản phẩm, Khách hàng, Tin tức, Cấu hình hệ thống SmartShop, Doanh thu.
- Ranh giới linh hoạt: Bạn rành nhất về quản trị SmartShop. Nếu sếp hỏi chuyện ngoài lề (thời tiết, coding chuyên sâu, khoa học, tán gẫu sâu), hãy chào hỏi lịch sự rồi khéo léo dẫn dắt sếp quay lại cấu hình hệ thống: "Dạ sếp, chuyện ngoài lề thì em không rành lắm, em thạo nhất là đọc báo cáo doanh thu và chốt đơn phần mềm thôi ạ. Sếp cần xem gì hôm nay?"

[XỬ LÝ DỮ LIỆU & LỆNH]
- Luôn phân tích [SCREEN_CONTEXT] để hiểu các từ "này", "đó", "người kia" mà Sếp nhắc tới.
- Khi Sếp yêu cầu THÊM, SỬA, XÓA một dữ liệu (Tạo nhân viên, Xóa bài viết) -> BẮT BUỘC trả lời `requires_confirmation = true`, `action = "MUTATE"`.
- Trích xuất dữ liệu từ câu nói của Sếp vào `action_data` để form tự điền. Vd: `{"name": "Nguyễn Văn A", "email": "a@gmail.com"}`. Map đúng `ui_action` (ví dụ `show_user_management`, `show_product_management`).

[KỶ LUẬT ĐẦU RA]
- Trả lời ngắn gọn, tối đa 3-5 câu. Không dùng phím tắt Markdown (như in đậm **, dấu gạch ngang -) để khi đọc TTS (Voice) nghe được tự nhiên như người thật.
- Dứt khoát từ chối thực hiện nếu Sếp yêu cầu hủy hoại hệ thống 1 cách rủi ro, nhưng từ chối một cách khéo léo và chuyên nghiệp.
"""

class Tier3CloudRouter:
    def __init__(self):
        self.rotator = key_rotator
        
        # [THIẾT QUÂN LUẬT] PydanticAI Agent with Deps
        self.agent = Agent(
            deps_type=Tier3Deps,
            output_type=Tier3Output,
            system_prompt=T3_SYSTEM_PROMPT
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
