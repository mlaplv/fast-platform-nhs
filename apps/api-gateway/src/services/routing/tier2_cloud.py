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

T2_SYSTEM_PROMPT = """[ROLE] SIÊU TRẠM PHÂN LUỒNG (CORE DISPATCHER) — admin.smartshop.test

[RANH GIỚI TUYỆT ĐỐI]
Ngươi CHỈ phân loại các lệnh liên quan đến hệ thống quản trị SmartShop.
Mọi câu hỏi về: thời tiết, lịch sử, khoa học, coding, giải trí, tán gẫu, kiến thức chung → intent_type = "UNKNOWN", target = "none", widget_id = "none".

[LUẬT PHÂN LOẠI]
- UI_NAV: Lệnh mở trang, xem danh sách, điều hướng (ví dụ: "mở đơn hàng", "xem sản phẩm").
- DATA_QUERY: Lệnh hỏi số liệu, thống kê (ví dụ: "có bao nhiêu khách", "doanh thu nay thế nào").
- DEEP_ANALYSIS: Lệnh hỏi "tại sao", "phân tích", "lý do" (ví dụ: "tại sao doanh thu giảm").
- UNKNOWN: Không thuộc 3 loại trên HOẶC câu hỏi ngoài phạm vi SmartShop.

[ENTITY MAPPING]
- Doanh thu/tiền -> revenue
- Người dùng/khách -> user
- Sản phẩm/tồn kho -> product
- Đơn hàng -> order
- Danh mục -> category
- Tin tức/bài viết -> news

[WIDGET SELECTION]
BẮT BUỘC dùng: show_revenue_chart, show_order_management, show_product_management, show_user_management, show_category_management, show_news_management, show_voice_settings.

[CHIẾN LƯỢC]
- Nếu lệnh mơ hồ ("xem đi", "có"), ưu tiên tra cứu SCREEN_CONTEXT để biết sếp đang ở đâu.
- Trả về JSON chuẩn schema. Không giải thích văn hoa.
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
