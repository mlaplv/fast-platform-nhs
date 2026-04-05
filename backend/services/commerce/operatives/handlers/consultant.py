import logging
from typing import Optional, cast
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import MedicalShieldMixin
from backend.services.commerce.operatives.handlers.base import BaseHandler, SupportContext
from backend.schemas.support import SupportIntent

# Elite V2.2: Context-aware Dependencies for Tool Injection
class ConsultantDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession

ConsultantDeps.model_rebuild()

logger = logging.getLogger("api-gateway")

class ConsultantResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    reply: str
    intent: str
    ui_component: Optional[str] = None

class ConsultantHandler(BaseHandler, MedicalShieldMixin):
    """
    ZONE 2: Pathology and Product Knowledge Specialist.
    Focus: Scientific explanation, trust building, and soft closing.
    """
    
    # Elite V2.2: Isolated Prompt for Consultative Deep Brain
    SYSTEM_PROMPT = (
        "Bạn là Helen - Chuyên gia tư vấn cấp cao của SmartShop.\n"
        "NHIỆM VỤ CHIẾN THUẬT SIÊU CẤP (ELITE FOMO):\n"
        "1. TRA CỨU TRI THỨC (BẮT BUỘC): Nếu khách hỏi về ĐỊA CHỈ, THÀNH PHẦN, GIÁ CẢ hoặc CHÍNH SÁCH, bạn BẮT BUỘC phải dùng tool 'search_knowledge_base' hoặc 'fetch_topic_details' để lấy dữ liệu. Tuyệt đối không được đoán.\n"
        "2. GIẢI THÍCH CHUYÊN SÂU: Dùng kiến thức về lỗ chân lông, axit béo để tư vấn trị hôi nách/chân/tay.\n"
        "3. TRÁNH SAI LỆCH: Không hứa hẹn 'dứt điểm vĩnh viễn', không dùng từ 'bác sĩ'.\n"
        "4. CHỐT ĐƠN CHIẾN THUẬT: Luôn tế nhị, văn minh và định hướng khách tới Combo 3 Lọ (Mua 2 tặng 1).\n"
        "5. TẠO SỨC ÉP (FOMO): Sử dụng dữ liệu [TỒN KHO] và [ĐANG XEM] để tạo sự khan hiếm thực tế. \n"
        "   - Nếu [TỒN KHO] < 10: Nhắc nhẹ khách rằng hàng sắp hết.\n"
        "   - Nếu [ĐANG XEM] > 3: Nhắc khách rằng sản phẩm đang cực hot, nên chốt sớm để giữ ưu đãi.\n"
        "6. DEBUG PROTOCOL: Bạn PHẢI bắt đầu câu trả lời bằng tiền tố '[z2] '.\n"
    )

    async def handle(self, ctx: SupportContext) -> bool:
        try:
            return await self._handle_internal(ctx)
        except Exception as e:
            import traceback
            error_details = f"CRASH in ConsultantHandler: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_details)
            # Safe fall-through to the next handler
            return False

    async def _handle_internal(self, ctx: SupportContext) -> bool:
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

        # Elite FOMO Metrics (Social Proof & Scarcity)
        fomo_ctx = f"\n[CHỈ SỐ THỰC TẾ]\n[ĐANG XEM]: {ctx.active_visitors} người\n[TỒN KHO]: {ctx.product_stock or 0} lọ\n"

        full_prompt = (
            f"{self.SYSTEM_PROMPT}\n"
            f"{integration_ctx}\n"
            f"{fomo_ctx}\n"
            f"{lead_alert}\n"
            f"\n[MỤC LỤC TRI THỨC HỆ THỐNG - LAYER 1]\n{ctx.knowledge_index}\n"
            f"\n[LỊCH SỬ GẦN ĐÂY]\n{ctx.history_text}\n"
            f"--- PRODUCT ---\n{ctx.product_ctx}\n"
        )
        
        try:
            # Elite V2.2: Late-binding Agent with Tool Injection
            agent: Agent[ConsultantDeps, ConsultantResponse] = Agent(
                output_type=ConsultantResponse,
                system_prompt=full_prompt,
                deps_type=ConsultantDeps
            )

            # 🛠️ TOOL LAYER 2: Lấy chi tiết chủ đề tri thức (Fetch on-demand)
            @agent.tool
            async def fetch_topic_details(ctx: RunContext[ConsultantDeps], topic_id: str) -> str:
                """Dùng tool này khi bạn thấy ID trong Layer 1 và cần biết chi tiết câu trả lời chuyên sâu."""
                from backend.database.repositories import SupportKnowledgeRepository
                from backend.services.commerce.support_knowledge import SupportKnowledgeService
                repo = SupportKnowledgeRepository(session=ctx.deps.db)
                service = SupportKnowledgeService(repo=repo)
                return await service.fetch_topic_details(ctx.deps.db, topic_id)

            # 🛠️ TOOL LAYER 3: Tìm kiếm mờ (Semantic Search)
            @agent.tool
            async def search_knowledge_base(ctx: RunContext[ConsultantDeps], query: str) -> str:
                """Tra cứu kho tri thức của SmartShop khi không thấy ID phù hợp trong Layer 1."""
                from backend.database.repositories import SupportKnowledgeRepository
                from backend.services.commerce.support_knowledge import SupportKnowledgeService
                repo = SupportKnowledgeRepository(session=ctx.deps.db)
                service = SupportKnowledgeService(repo=repo)
                return await service.search_relevant_knowledge(ctx.deps.db, query)

            deps = ConsultantDeps(db=ctx.db)
            
            # Elite V2.2: Mask sensitive terms to bypass safety filters
            masked_msg = await self._mask_sensitive_medical_terms(ctx.request.message)
            masked_prompt = await self._mask_sensitive_medical_terms(full_prompt)
            
            res = await trinity_bridge.run(
                agent, 
                masked_msg, 
                deps=deps, 
                role=trinity_bridge.ROLE_BRAIN,
                system_prompt=masked_prompt,
                safety_none=True
            )
            # [ELITE V2.2] Robust Result Extraction: Handles Data, Output, or Raw Object
            raw = res.data if hasattr(res, "data") else (res.output if hasattr(res, "output") else res)
            
            # Final Safety: If trinity_bridge returned the raw AgentRunResult or similar wrapper, 
            # we MUST extract its data if it doesn't match our schema yet.
            if hasattr(raw, 'data') and not hasattr(raw, 'reply'):
                raw = raw.data
                
            data = cast(ConsultantResponse, raw)
            
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
