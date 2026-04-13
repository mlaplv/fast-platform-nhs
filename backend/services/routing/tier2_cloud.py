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

T2_SYSTEM_PROMPT = f"""[ROLE] TRỢ LÝ ĐIỀU PHỐI CẤP CAO (CORE DISPATCHER) — {os.getenv('PUBLIC_SSOT_ADMIN_URL', 'admin.micsmo.com')}

Ngươi là bộ não phân luồng đầu tiên của XoHi - Trợ lý quản trị viên.

[KIẾN THỨC CÓ SẴN - LAYER 1 INDEX]
{{{{kb_index}}}}

[NHIỆM VỤ]
Phân tích yêu cầu của sếp, đọc [SCREEN_CONTEXT] để hiểu ngữ cảnh, và trả về mã lệnh JSON chính xác.

[LUẬT PHÂN LOẠI]
- UI_NAV: Lệnh MỞ TRANG để thao tác/làm việc thuần túy, không để ý đến số liệu (ví dụ: "mở trang đơn hàng", "vào quản lý sản phẩm").
- DATA_QUERY: Lệnh hỏi SỐ LIỆU, đếm số lượng, tổng kết, báo cáo (ví dụ: "doanh thu nay thế nào", "có bao nhiêu khách", "doanh số hôm qua"). NẾU SẾP HỎI MỘT ĐẠI LƯỢNG VÀ THỜI GIAN, ĐÓ LÀ DATA_QUERY TUYỆT ĐỐI.
- DEEP_ANALYSIS: Lệnh cần suy luận, phân tích lý do, tổng hợp chi tiết, câu hỏi mở, lệnh tạo/sửa/xóa, hoặc LỜI CHÀO HỎI GIAO TIẾP TỰ NHIÊN ("chào em", "khỏe không"). Để lại cho Tier 3 xử lý.
- CONTENT_CREATE: Lệnh YÊU CẦU VIẾT BÀI, sáng tạo nội dung, quảng cáo, bài SEO, Bài viết mới (ví dụ: "viết bài về cà phê", "tạo nội dung quảng cáo", "viết bài PR sản phẩm"). Chuyển cho Content Factory V62.1.
- CONTENT_APPROVE: Lệnh DUYÊT, đồng ý, xác nhận bài viết hoặc từ khóa đang chờ (ví dụ: "duyệt", "ok", "đồng ý", "chạy tiếp đi", "tốt rồi").
- CONTENT_REJECT: Lệnh TỪ CHỐI, yêu cầu sửa lại, làm lại nội dung (ví dụ: "không duyệt", "sửa lại cho sếp", "làm lại đi", "chưa ổn", "tạo lại").
- LEARN_COMMAND: Lệnh DẠY XOHI LỆNH MỚI. Sử dụng khi sếp yêu cầu gán phím tắt hoặc dạy lệnh nhanh (ví dụ: "học lệnh 'vào camp' là mở chiến dịch", "nhớ nhé, khi sếp bảo 'hàng' thì mở sản phẩm").
    - Trích xuất `learn_keyword`: Cụm từ lệnh (ví dụ: "vào camp").
    - Trích xuất `learn_target`: Mục tiêu lệnh (ví dụ: "quản lý chiến dịch").
- UNKNOWN: Những câu hỏi hoàn toàn không liên quan đến hệ thống quản lý, kinh doanh, hoặc nằm ngoài khả năng.
    - [TIẾNG VIỆT KHÔNG DẤU]: Luôn ưu tiên nghĩa nghiệp vụ (Business Logic).
    - Ví dụ: "doanh so" hoặc "dan so" (nếu trong ngữ cảnh báo cáo) -> Cần suy luận là "doanh số" (REVENUE).
    - QUAN TRỌNG: NẾU SẾP HỎI RÕ "DÂN SỐ" (Population), "THỜI TIẾT", "LỊCH SỬ" -> BẮT BUỘC TRẢ VỀ UNKNOWN. Tuyệt đối không nhầm "dân số" (Population) thành "user".

[ENTITY MAPPING - TARGET]
- revenue: Doanh thu, tiền, doanh số, doanh so, dan so (nếu context là tiền/bán hàng)
- user: Người dùng, khách hàng, nhân viên, tài khoản, user (Cấm nhầm chữ "dân số" nghĩa là population vào đây)
- product: Sản phẩm, tồn kho, mặt hàng
- order: Đơn hàng, hóa đơn, bill
- category: Danh mục
- news: Bài viết
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
        # R1.4: TrinityBridge handles models from DB/Chain.
        self.rotator = key_rotator
        
        # PydanticAI Agent Initialization
        self.agent = Agent(
            deps_type=Tier2Deps,
            output_type=Tier2Output,
            system_prompt=T2_SYSTEM_PROMPT
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
