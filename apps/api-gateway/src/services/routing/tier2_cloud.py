import asyncio
import json
import logging
import os
from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from litellm import RateLimitError, AuthenticationError, ServiceUnavailableError, Timeout as LiteLLMTimeout

from shared.schemas.intent import IntentResponse, IntentAction, RouterTier
from ai_engine.core.key_rotator import SmartKeyRotator

logger = logging.getLogger("api-gateway")

class Tier2Output(BaseModel):
    """Structured output for Tier 2 Dispatcher extraction."""
    intent_type: Literal["UI_NAV", "DATA_QUERY", "DEEP_ANALYSIS", "UNKNOWN"] = Field(
        description="Type of user intent classification"
    )
    target: Literal["order", "revenue", "product", "user", "category", "news", "none"] = Field(
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

# R1.6: Cache schema at Global Scope — CẤM tạo lại mỗi request
TIER2_SCHEMA = Tier2Output.model_json_schema()

from dataclasses import dataclass

@dataclass
class Tier2Deps:
    """Dependencies for Tier 2 Dispatcher."""
    screen_context: Optional[dict] = None
    rotator: Optional[SmartKeyRotator] = None

T2_SYSTEM_PROMPT = """[ROLE] TRỢ LÝ ĐIỀU PHỐI CẤP CAO (CORE DISPATCHER) — admin.smartshop.test

Ngươi là bộ não phân luồng đầu tiên của XoHi - Trợ lý quản trị viên.

[NHIỆM VỤ]
Phân tích yêu cầu của sếp, đọc [SCREEN_CONTEXT] để hiểu ngữ cảnh, và trả về mã lệnh JSON chính xác.

[LUẬT PHÂN LOẠI]
- UI_NAV: Lệnh mở trang, xem danh sách, điều hướng đơn thuần (ví dụ: "mở đơn hàng", "xem sản phẩm").
- DATA_QUERY: Lệnh hỏi số liệu, đếm số lượng, tổng kết (ví dụ: "doanh thu nay thế nào", "có bao nhiêu khách", "hôm qua bán được không").
- DEEP_ANALYSIS: Lệnh cần suy luận, phân tích lý do, tổng hợp chi tiết, câu hỏi mở, lệnh tạo/sửa/xóa, hoặc LỜI CHÀO HỎI GIAO TIẾP TỰ NHIÊN ("chào em", "khỏe không"). Để lại cho Tier 3 xử lý.
- UNKNOWN: Những câu hỏi hoàn toàn không liên quan đến hệ thống quản lý, kinh doanh, hoặc nằm ngoài khả năng (ví dụ: thời tiết, tin tức thế giới, khoa học).

[ENTITY MAPPING - TARGET]
- revenue: Doanh thu, tiền, doanh số
- user: Người dùng, khách hàng, nhân viên, tài khoản
- product: Sản phẩm, tồn kho, mặt hàng
- order: Đơn hàng, hóa đơn, bill
- category: Danh mục
- news: Tin tức, bài viết
- none: Không rõ hoặc không liên quan.

[TIMEFRAME MAPPING]
- today: Hôm nay, nay, ngày này.
- this_week: Tuần này, tuần nay.
- this_month: Tháng này, tháng nay.
- none: Toàn thời gian, không đề cập. Khéo léo nhìn vào lịch sử hội thoại nếu câu hỏi nối tiếp.

[WIDGET SELECTION]
Chọn 1 trong các widget: show_revenue_chart, show_order_management, show_product_management, show_user_management, show_category_management, show_news_management, show_voice_settings. Nếu không cần, chọn `none`. 

[CHIẾN LƯỢC QUAN TRỌNG]
- Thông minh: Đọc [SCREEN_CONTEXT] (nếu có) để bắt nội dung đang hiển thị. "Xem chi tiết", "xóa cái này" > dựa vào màn hình.
- Kỷ luật: Chỉ trả về JSON hợp lệ tuyệt đối, không giải thích dài dòng.
"""

class Tier2CloudRouter:
    def __init__(self):
        # R1.4: Single Source of Truth from .env
        self.primary_model_name = os.getenv("TIER2_MODEL", "gemini/gemini-1.5-flash")
        self.fallback_model_name = os.getenv("TIER2_FALLBACK_MODEL", "gemini/gemini-2.0-flash")
        self.rotator = SmartKeyRotator()
        
        # PydanticAI Agent Initialization
        self.agent = Agent(
            model=self.primary_model_name,
            deps_type=Tier2Deps,
            output_type=Tier2Output,
            system_prompt=T2_SYSTEM_PROMPT
        )

        @self.agent.system_prompt
        def add_context(ctx: RunContext[Tier2Deps]) -> str:
            if ctx.deps.screen_context:
                return f"\n[SCREEN_CONTEXT]\n{json.dumps(ctx.deps.screen_context, ensure_ascii=False)}"
            return ""

    async def extract(self, transcript: str, context: list = None, screen_context: dict | None = None) -> Optional[IntentResponse]:
        # R1.8: Anti-Blocking — Truncate transcript to protect event loop
        transcript = transcript[:500]

        # Clean up context for PydanticAI
        history = []
        if context:
            for msg in context:
                if msg.get("role") != "system":
                    history.append(msg)
        
        all_keys = self.rotator.get_all_keys()
        max_tries = min(len(all_keys), 3)
        model_names = [self.primary_model_name, self.fallback_model_name]
        
        deps = Tier2Deps(screen_context=screen_context, rotator=self.rotator)

        for model_name in model_names:
            for attempt in range(max_tries):
                api_key = self.rotator.get_next_key()
                os.environ["GEMINI_API_KEY"] = api_key
                os.environ.pop("GOOGLE_API_KEY", None) # R1.4 SSOT: Prevent LiteLLM conflict
                
                try:
                    result = await self.agent.run(
                        transcript,
                        message_history=history,
                        model=model_name,
                        deps=deps
                    )
                    
                    output: Tier2Output = result.data
                    action_map = {
                        "UI_NAV": IntentAction.READ, 
                        "DATA_QUERY": IntentAction.COUNT, 
                        "DEEP_ANALYSIS": IntentAction.ANALYZE, 
                        "UNKNOWN": IntentAction.READ
                    }
                    action = action_map.get(output.intent_type, IntentAction.READ)

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
                            "status": output.status
                        }
                    )
                except (ServiceUnavailableError, RateLimitError, LiteLLMTimeout, AuthenticationError) as e:
                    logger.warning(f"[T2 Dispatcher] {model_name} attempt {attempt+1} failed ({type(e).__name__}). Rotating...")
                    if attempt < max_tries - 1:
                        await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                except Exception as e:
                    logger.error(f"[T2 Dispatcher] Critical error: {e}")
                    raise e

            logger.warning(f"[T2 Dispatcher] {model_name} exhausted {max_tries} keys. Falling back...")

        return None
