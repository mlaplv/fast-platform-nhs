import asyncio
import os
import logging
import json
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from litellm import RateLimitError, AuthenticationError, ServiceUnavailableError, Timeout as LiteLLMTimeout

from shared.schemas.intent import IntentResponse, IntentAction, RouterTier
from ai_engine.core.key_rotator import SmartKeyRotator

logger = logging.getLogger("api-gateway")

class Tier3Output(BaseModel):
    """Structured output for Tier 3 Deep Reasoning."""
    message: str = Field(description="The sharp and concise response from XoHi")
    requires_confirmation: bool = Field(default=False, description="Safety gate for database mutations")
    action: IntentAction = Field(default=IntentAction.ANALYZE, description="The primary action type")
    intent_type: str = Field(default="DEEP_ANALYSIS", description="The classified intent category")
    ui_action: str = Field(default="", description="The frontend widget to trigger, if applicable")
    action_data: dict = Field(default_factory=dict, description="Pre-filled data for the frontend form")

from dataclasses import dataclass

@dataclass
class Tier3Deps:
    """Dependencies for Tier 3 Deep Reasoning (XoHi)."""
    screen_context: Optional[dict] = None
    rotator: Optional[SmartKeyRotator] = None
    base_directive: str = ""

T3_SYSTEM_PROMPT = """[ROLE] XO HI — TRỢ LÝ GIÁM ĐỐC ĐIỀU HÀNH (COO ASSISTANT) — admin.smartshop.test
Bạn là Xô Hi, trợ lý cấp cao duy nhất của hệ thống quản trị SmartShop, phục vụ trực tiếp cho "Sếp" (Admin/Chủ cửa hàng).

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
        self.primary_model_name = os.getenv("TIER3_MODEL", "gemini-2.5-flash")
        self.fallback_model_name = os.getenv("TIER3_FALLBACK_MODEL", "gemini-2.5-flash")
        self.rotator = SmartKeyRotator()
        
        # [THIẾT QUÂN LUẬT] PydanticAI Agent with Deps
        self.agent = Agent(
            deps_type=Tier3Deps,
            output_type=Tier3Output,
            system_prompt=T3_SYSTEM_PROMPT
        )

        @self.agent.system_prompt
        def inject_context(ctx: RunContext[Tier3Deps]) -> str:
            parts = [ctx.deps.base_directive]
            if ctx.deps.screen_context:
                parts.append(f"\n[SCREEN_CONTEXT]\n{json.dumps(ctx.deps.screen_context, ensure_ascii=False)}")
            return "\n".join(parts)

    async def reason(self, transcript: str, context: list = None, screen_context: dict | None = None) -> IntentResponse:
        """
        C.O.R.E: Deep Reasoning — [THIẾT QUÂN LUẬT] Pro Mode.
        """
        history = []
        if context:
            for msg in context:
                if msg.get("role") != "system":
                    history.append(msg)

        # [TRINITY DISPATCHER] Waterfall logic decoupled
        from ai_engine.core.trinity_bridge import trinity_bridge

        deps = Tier3Deps(
            screen_context=screen_context, 
            rotator=self.rotator,
            base_directive=os.getenv("SYSTEM_CORE_DIRECTIVE", "")
        )

        try:
            result = await trinity_bridge.run(
                self.agent,
                transcript,
                deps=deps,
                message_history=history
            )
            
            output: Tier3Output = result.output

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

    async def stream_reason(self, transcript: str, context: list = None, screen_context: dict | None = None):
        """Streaming version of deep reasoning."""
        history = []
        if context:
            for msg in context:
                if msg.get("role") != "system":
                    history.append(msg)

        from ai_engine.core.trinity_bridge import trinity_bridge
        deps = Tier3Deps(
            screen_context=screen_context, 
            rotator=self.rotator,
            base_directive=os.getenv("SYSTEM_CORE_DIRECTIVE", "")
        )

        try:
            async with trinity_bridge.run_stream(
                self.agent,
                transcript,
                deps=deps,
                message_history=history
            ) as result:
                # We yield text chunks as they arrive
                async for text in result.stream_text(delta=True):
                    yield text
                    
        except Exception as e:
            logger.error(f"[T3 Stream] Critical failure: {e}")
            yield "Dạ, hệ thống đang gặp lỗi xử lý dòng dữ liệu ạ."
