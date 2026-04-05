import logging
from typing import Optional, cast
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.schemas.support import SupportIntent

# Elite V2.2: Context-aware Dependencies for Tool Injection
class ConsultantDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession

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
        "Bạn là Helen - Chuyên gia tư vấn cấp cao của SmartShop.\n"
        "NHIỆM VỤ CHIẾN THUẬT:\n"
        "1. TRA CỨU TRI THỨC: Nếu khách hỏi về địa chỉ, thành phần, giá cả hoặc chính sách, hãy dùng tool 'search_knowledge_base' để lấy dữ liệu chuẩn sòng phẳng.\n"
        "2. GIẢI THÍCH CHUYÊN SÂU: Dùng kiến thức về lỗ chân lông, axit béo để tư vấn trị hôi nách/chân/tay.\n"
        "3. TRÁNH SAI LỆCH: Không hứa hẹn 'dứt điểm vĩnh viễn', không dùng từ 'bác sĩ'.\n"
        "4. CHUYÊN NGHIỆP: Luôn tế nhị, văn minh và định hướng khách tới Combo 3 Lọ (Mua 2 tặng 1).\n"
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
            # Elite V2.2: Late-binding Agent with Tool Injection
            agent: Agent[ConsultantDeps, ConsultantResponse] = Agent(
                result_type=ConsultantResponse,
                system_prompt=full_prompt,
                deps_type=ConsultantDeps
            )

            # 🛠️ Gắn Tool tìm kiếm tri thức (Hàng nóng của Sếp)
            @agent.tool
            async def search_knowledge_base(ctx: RunContext[ConsultantDeps], query: str) -> str:
                """Tra cứu kho tri thức của SmartShop về địa chỉ, thành phần, chính sách..."""
                from backend.database.repositories import SupportKnowledgeRepository
                from backend.services.commerce.support_knowledge import SupportKnowledgeService
                repo = SupportKnowledgeRepository(session=ctx.deps.db)
                service = SupportKnowledgeService(repo=repo)
                return await service.search_relevant_knowledge(ctx.deps.db, query)

            deps = ConsultantDeps(db=ctx.db)
            res = await trinity_bridge.run(agent, ctx.request.message, deps=deps, role=trinity_bridge.ROLE_BRAIN)
            data = cast(ConsultantResponse, res.data)
            
            if data and data.reply:
                ctx.replies.append(data.reply)
                # Ensure intent matches SupportIntent enum values safely
                valid_intents = {i.value for i in SupportIntent}
                ctx.intent = SupportIntent(data.intent) if data.intent in valid_intents else SupportIntent.PRODUCT_QUERY
                ctx.ui_component = data.ui_component
                return True 
            
            return False # Fallback if AI output is invalid
            
        except Exception as e:
            logger.error(f"[ConsultantHandler] Sweep Failure: {e}")
            return False
