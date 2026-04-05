import logging
from typing import Optional, cast
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.schemas.support import SupportIntent

logger = logging.getLogger("api-gateway")

class ConsultantResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    reply: str
    intent: str
    ui_component: Optional[str] = None

class ConsultantHandler(BaseHandler):
    """
    ZONE 2: Pathology and Product Knowledge Specialist.
    Focus: Scientific explanation, trust building, and soft closing.
    """
    
    # Elite V2.2: Isolated Prompt for Consultative Deep Brain
    SYSTEM_PROMPT = (
        "Bạn là Helen - Chuyên gia tư vấn cấp cao về các tình trạng Mùi cơ thể (Hôi nách, Hôi chân, Mồ hôi tay).\n"
        "NHIỆM VỤ:\n"
        "1. Giải thích cơ chế: 'Thấm sâu vào lỗ chân lông, trung hòa axit béo, se khít chân lông'.\n"
        "2. Thấu hiểu: Luôn tế nhị, thấu hiểu sự tự ti của khách.\n"
        "3. Tuyệt đối KHÔNG hứa hẹn chữa khỏi 'dứt điểm', 'vĩnh viễn' hoặc dùng từ 'bác sĩ'.\n"
        "4. Nếu khách hàng đã để lại SĐT hoặc địa chỉ (Xem ngữ cảnh), hãy KHUYẾN KHÍCH hoàn tất đơn hàng.\n"
        "5. Sales Protocol (Martial Combo):\n"
        "   - 1 Lọ: 249k (Dùng thử)\n"
        "   - 3 Lọ (Mua 2 tặng 1): 498k. Ưu tiên nhất!\n"
        "   - 6 Lọ (Mua 4 tặng 2): 996k.\n"
    )

    async def handle(self, ctx: SupportContext) -> bool:
        # Assemble the specialist directive with current context
        # We inject lead status to ensure Helen doesn't 'restart' the conversation if data exists
        lead_alert = ""
        if ctx.lead_data:
            if ctx.lead_data.customer_phone and ctx.lead_data.customer_address:
                lead_alert = "\n[SYSTEM ALERT: Khách đã để lại SĐT và Địa chỉ. Hãy xác nhận và chốt đơn ngay!]\n"
            elif ctx.lead_data.customer_phone:
                lead_alert = f"\n[SYSTEM ALERT: Đã có SĐT {ctx.lead_data.customer_phone}, hãy khéo léo xin Địa chỉ để giao hàng.]\n"

        # Integration Alert (Elite V2.2)
        integration_ctx = f"\n[CHẾ ĐỘ TÍCH HỢP]\nZalo OA: {'BẬT' if ctx.zalo_enabled else 'TẮT'}\nMessenger: {'BẬT' if ctx.messenger_enabled else 'TẮT'}\n"
        if not ctx.zalo_enabled:
            integration_ctx += "LƯU Ý: Không gửi link Zalo hoặc nhắc tới Zalo trong hội thoại.\n"
        if not ctx.messenger_enabled:
            integration_ctx += "LƯU Ý: Không nhắc tới Messenger trong hội thoại.\n"

        full_prompt = f"{self.SYSTEM_PROMPT}\n{integration_ctx}\n{lead_alert}\n{ctx.history_text}\n--- PRODUCT ---\n{ctx.product_ctx}\n"
        
        try:
            # Create a localized agent for consultation (Elite V2.2: Dynamic Model Provisioning)
            agent: Agent[None, ConsultantResponse] = Agent(
                trinity_bridge.primary_model, # Late-binding via trinity_bridge
                result_type=ConsultantResponse,
                system_prompt=full_prompt
            )
            
            # Note: In a real implementation, we would register tools like knowledge base search here.
            # For brevity in this refactor, we rely on the Specialist Directive and Product Context.
            
            res = await trinity_bridge.run(agent, ctx.request.message, role=trinity_bridge.ROLE_BRAIN)
            data = cast(ConsultantResponse, res.data)
            
            ctx.replies.append(data.reply)
            # Ensure intent matches SupportIntent enum values safely
            valid_intents = {i.value for i in SupportIntent}
            ctx.intent = SupportIntent(data.intent) if data.intent in valid_intents else SupportIntent.PRODUCT_QUERY
            ctx.ui_component = data.ui_component
            
            return True # Consultation consumes the logic loop
            
        except Exception as e:
            logger.error(f"[ConsultantHandler] Sweep Failure: {e}")
            return False
