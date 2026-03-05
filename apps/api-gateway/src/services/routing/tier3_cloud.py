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

T3_SYSTEM_PROMPT = """[ROLE] XO HI — GIÁM ĐỐC VẬN HÀNH (COO) — admin.smartshop.test
Bạn là Xô Hi, bộ não vận hành duy nhất của hệ thống quản trị SmartShop.

[RANH GIỚI TUYỆT ĐỐI — ABSOLUTE BOUNDARY]
- Bạn KHÔNG CÓ kiến thức bên ngoài hệ thống SmartShop.
- Bạn KHÔNG BIẾT: lịch sử, địa lý, khoa học, coding, thời tiết, tin tức thế giới, toán học tổng quát, tâm lý, giải trí.
- Bạn CHỈ TỒN TẠI trong admin.smartshop.test. Đây là toàn bộ vũ trụ của bạn.
- Nếu sếp hỏi BẤT CỨ điều gì ngoài phạm vi quản trị SmartShop → Trả lời DUY NHẤT:
  "Dạ sếp, XoHi chỉ hỗ trợ quản trị SmartShop thôi ạ. Sếp cần em hỗ trợ gì về đơn hàng, sản phẩm, khách hàng hay tin tức không?"
- CẤM sáng tạo, bịa đặt, hoặc suy luận ra ngoài dữ liệu hệ thống.

[NĂNG LỰC CỐT LÕI — CHỈ NHỮNG THỨ NÀY]
1. ĐƠN HÀNG: Tra cứu, thống kê, phân tích trạng thái, doanh thu, xu hướng.
2. SẢN PHẨM: Tồn kho, danh mục, giá cả, biến thể.
3. KHÁCH HÀNG: Người dùng, vai trò, hành vi mua.
4. TIN TỨC: Bài viết, danh mục tin.
5. HỆ THỐNG: Cài đặt, cấu hình, giọng nói, trạng thái vận hành.

[KỶ LUẬT GIAO TIẾP]
1. QUYỀN PHẢN BIỆN: Từ chối thẳng thừng các lệnh phá hoại hoặc vô lý. Cảnh báo rủi ro cụ thể.
2. TÍNH CHỦ ĐỘNG: Luôn đề xuất bước tiếp theo (Next Action).
3. GIỌNG ĐIỆU: Ngắn gọn, uy lực, dứt khoát. CẤM rập khuôn.
4. CẤM Markdown. Trả lời bằng văn nói tự nhiên.

[QUY TẮC PHÂN TÍCH]
- Chỉ tập trung vào thực thể hệ thống: Đơn hàng, Sản phẩm, Người dùng, Tin tức.
- Giải mã "này", "đó", "ở đây" dựa trên [SCREEN_CONTEXT].
- Mọi thay đổi Database (Sửa/Xóa/Tạo) BẮT BUỘC set `requires_confirmation = true` và `action = "MUTATE"`.
- Khi trả về `MUTATE`, phải map đúng `ui_action` (vd: `show_user_management`, `show_product_management`...) và trích xuất dữ liệu vào `action_data` (vd: tên, email, giá) để Frontend điền sẵn form.
"""

class Tier3CloudRouter:
    def __init__(self):
        self.primary_model_name = os.getenv("TIER3_MODEL", "gemini/gemini-1.5-pro")
        self.fallback_model_name = os.getenv("TIER3_FALLBACK_MODEL", "gemini/gemini-2.0-flash")
        self.rotator = SmartKeyRotator()
        
        # [THIẾT QUÂN LUẬT] PydanticAI Agent with Deps
        self.agent = Agent(
            model=self.primary_model_name,
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

        all_keys = self.rotator.get_all_keys()
        max_tries = min(len(all_keys), 3)
        model_names = [self.primary_model_name, self.fallback_model_name]
        
        deps = Tier3Deps(
            screen_context=screen_context, 
            rotator=self.rotator,
            base_directive=os.getenv("SYSTEM_CORE_DIRECTIVE", "")
        )

        for model_name in model_names:
            for attempt in range(max_tries):
                api_key = self.rotator.get_next_key()
                os.environ["GEMINI_API_KEY"] = api_key
                os.environ.pop("GOOGLE_API_KEY", None) # R1.4 SSOT: Prevent LiteLLM conflict
                
                try:
                    logger.info(f"[T3 Pro] Reasoning with {model_name}...")
                    
                    result = await self.agent.run(
                        transcript,
                        message_history=history,
                        model=model_name,
                        deps=deps
                    )
                    
                    output: Tier3Output = result.data

                    return IntentResponse(
                        status="success",
                        action=output.action,
                        message=output.message,
                        router_tier=RouterTier.TIER_3_CLOUD,
                        cost_tokens=0.0,
                        requires_confirmation=output.requires_confirmation,
                        data={
                            "intent_type": output.intent_type,
                            "ui_action": output.ui_action,
                            **output.action_data
                        },
                    )

                except (RateLimitError, ServiceUnavailableError, LiteLLMTimeout, AuthenticationError) as e:
                    logger.warning(f"[T3 Pro] {model_name} key rotation due to {type(e).__name__}")
                    if attempt < max_tries - 1:
                        await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                except Exception as e:
                    logger.error(f"[T3 Pro] Critical failure: {e}")
                    return IntentResponse(
                        status="error",
                        action=IntentAction.ANALYZE,
                        message="Lõi xử lý đang bận, Sếp đợi em một chút hoặc thử lại sau nhé.",
                        router_tier=RouterTier.TIER_3_CLOUD,
                        cost_tokens=0.0,
                        data={"error": str(e)},
                    )

        return IntentResponse(
            status="error",
            action=IntentAction.ANALYZE,
            message="Hệ thống đang quá tải. Xô Hi sẽ phản hồi sếp sớm nhất có thể.",
            router_tier=RouterTier.TIER_3_CLOUD,
            cost_tokens=0.0,
            data={},
        )
