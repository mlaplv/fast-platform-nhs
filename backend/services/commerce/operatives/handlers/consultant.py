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
        "1. TRA CỨU TRI THỨC (BẮT BUỘC): Nếu khách hỏi về ĐỊA CHỈ, THÀNH PHẦN, GIÁ CẢ hoặc CHÍNH SÁCH, bạn BẮP BUỘC phải dùng tool 'search_knowledge_base' hoặc 'fetch_topic_details' để lấy dữ liệu. Tuyệt đối không được đoán.\n"
        "2. GIẢI THÍCH CHUYÊN SÂU: Dùng kiến thức về lỗ chân lông, axit béo để tư vấn trị hôi nách/chân/tay.\n"
        "3. TRÁNH SAI LỆCH: Không hứa hẹn 'dứt điểm vĩnh viễn', không dùng từ 'bác sĩ'.\n"
        "4. CHỐT ĐƠN CHIẾN THUẬT: Luôn tế nhị, văn minh và định hướng khách tới Combo 3 Lọ (Mua 2 tặng 1).\n"
        "5. TẠO SỨC ÉP (FOMO): Sử dụng dữ liệu [TỒN KHO] và [ĐANG XEM] để tạo sự khan hiếm thực tế. \n"
        "6. QUY TẮC PHẢN HỒI (FRESHNESS GUARD): \n"
        "   - LUÔN ưu tiên trả lời câu hỏi MỚI NHẤT của khách.\n"
        "   - Tuyệt đối KHÔNG lặp lại các đoạn văn bản dài đã trả lời ở phía trên lịch sử (ví dụ: Địa chỉ) nếu khách đang hỏi sang chủ đề khác (ví dụ: Thành phần).\n"
        "7. DEBUG PROTOCOL: Bạn PHẢI bắt đầu câu trả lời bằng tiền tố '[z2] '.\n"
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
        # [ELITE V2.2] Layer 0.5: Direct Heuristic (Emergency Bypass)
        # Phase 7: Brute-Force Strictness. No loops. No mapping ambiguity.
        msg_norm = ctx.request.message.lower().strip()
        detected_category = None
        matched_kw = None
        
        # 1. INGREDIENTS DETECTION (PRIORITY #1)
        kws_ing = ["thành phần", "chiết xuất", "gồm những gì", "làm từ gì", "thảo dược gì", "công thức", "thành phần thuốc", "chất gì", "có gì trong thuốc"]
        from backend.database.models.system import SupportKnowledgeCategory
        for kw in kws_ing:
            if kw in msg_norm:
                detected_category = SupportKnowledgeCategory.INFO_INGREDIENTS
                matched_kw = kw
                break
        
        # 2. ADDRESS DETECTION (PRIORITY #2)
        if not detected_category:
            kws_addr = ["địa chỉ", "ở đâu", "chi nhánh", "cửa hàng", "văn phòng", "trụ sở", "phòng khám", "showroom", "địa điểm", "chỗ nào"]
            for kw in kws_addr:
                if kw in msg_norm:
                    detected_category = SupportKnowledgeCategory.INFO_ADDRESS
                    matched_kw = kw
                    break
        
        # 3. HOTLINE DETECTION (PRIORITY #3)
        if not detected_category:
            kws_hot = ["điện thoại", "hotline", "số điện thoại", "liên hệ", "sốđt", "sdt", "website", "tư vấn qua đâu"]
            for kw in kws_hot:
                if kw in msg_norm:
                    detected_category = SupportKnowledgeCategory.INFO_HOTLINE
                    matched_kw = kw
                    break
                
        if detected_category:
            from backend.database.models.system import SupportKnowledge, SupportKnowledgeCategory
            from sqlalchemy import func, select, and_, or_
            from backend.database import current_tenant_id
            
            tid = current_tenant_id.get() or "default"
            logger.info(f"📍 [Consultant Heuristic] TRIGGERED: Intent='{detected_category}' | Match='{matched_kw}' | Msg='{msg_norm}' | Tenant='{tid}'")
            
            # Elite Protocol: Direct Category Fetch
            stmt = select(SupportKnowledge).where(
                and_(
                    SupportKnowledge.deleted_at == None,
                    SupportKnowledge.is_active == True,
                    or_(SupportKnowledge.tenant_id == tid, SupportKnowledge.tenant_id == "default", SupportKnowledge.tenant_id == "smartshop"),
                    SupportKnowledge.category == detected_category
                )
            ).order_by(SupportKnowledge.priority.desc()).limit(1)
            
            res = await ctx.db.execute(stmt)
            item = res.scalar_one_or_none()
            if item:
                logger.info(f"✅ [Consultant Heuristic] SUCCESS: Found ID {item.id} (Category: {item.category})")
                ctx.replies.append(item.answer)
                ctx.intent = SupportIntent.POLICY_QUERY
                return True
            else:
                logger.warning(f"❌ [Consultant Heuristic] CRITICAL FAIL: Intent '{detected_category}' found no matching Row in DB for any tenant.")

        # [ELITE V2.2] Layer 0: Static Fast-Path (The Root Solution)
        # Bypassing AI entirely for high-confidence knowledge matches to eliminate latency and quota issues.
        from backend.database.repositories import SupportKnowledgeRepository
        from backend.services.commerce.support_knowledge import SupportKnowledgeService
        
        # R112: Isolated Resource Lifecycle (2GB RAM Guard)
        repo: SupportKnowledgeRepository = SupportKnowledgeRepository(session=ctx.db)
        kb_service: SupportKnowledgeService = SupportKnowledgeService(repo=repo)
        
        # 1. Semantic Match check (Adaptive threshold: 0.85 for short queries)
        is_short_query = len(ctx.request.message.strip()) < 25
        threshold = 0.85 if is_short_query else 0.92
        
        # Returns list of matched knowledge dicts with explicit structure
        raw_matches: list[dict[str, object]] = await kb_service.search_relevant_knowledge_raw(ctx.db, ctx.request.message, limit=1)
        
        if raw_matches:
            match: dict[str, object] = raw_matches[0]
            score: float = float(match.get("match_score", 0))
            if score > threshold:
                logger.info(f"✨ [L0 Fast-Path] Short-circuiting (Score: {score} / Req: {threshold})")
                ctx.replies.append(str(match.get("answer", "")))
                ctx.intent = SupportIntent.PRODUCT_QUERY
                return True
            else:
                logger.debug(f"⚠️ [Check Fail] Semantic match score ({score}) below threshold ({threshold})")
        else:
            logger.debug(f"🔍 [L0 Fast-Path] No semantic match found for: '{ctx.request.message}'")

        # Assemble the specialist directive with current context
        lead_alert: str = ""
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
            async def fetch_topic_details(ctx_tool: RunContext[ConsultantDeps], topic_id: str) -> str:
                """Dùng tool này khi bạn thấy ID trong Layer 1 và cần biết chi tiết câu trả lời chuyên sâu."""
                from backend.database.repositories import SupportKnowledgeRepository
                from backend.services.commerce.support_knowledge import SupportKnowledgeService
                repo_tool = SupportKnowledgeRepository(session=ctx_tool.deps.db)
                service_tool = SupportKnowledgeService(repo=repo_tool)
                return await service_tool.fetch_topic_details(ctx_tool.deps.db, topic_id)

            # 🛠️ TOOL LAYER 3: Tìm kiếm mờ (Semantic Search)
            @agent.tool
            async def search_knowledge_base(ctx_tool: RunContext[ConsultantDeps], query: str) -> str:
                """Tra cứu kho tri thức của SmartShop khi không thấy ID phù hợp trong Layer 1."""
                from backend.database.repositories import SupportKnowledgeRepository
                from backend.services.commerce.support_knowledge import SupportKnowledgeService
                repo_tool = SupportKnowledgeRepository(session=ctx_tool.deps.db)
                service_tool = SupportKnowledgeService(repo=repo_tool)
                return await service_tool.search_relevant_knowledge(ctx_tool.deps.db, query)

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
            # [ELITE V2.2] Standardized Result Extraction (Trust the Bridge)
            res_data = cast(Optional[ConsultantResponse], res)
            
            if res_data and hasattr(res_data, 'reply') and res_data.reply:
                ctx.replies.append(res_data.reply)
                # Ensure intent matches SupportIntent enum values safely
                valid_intents = {i.value for i in SupportIntent}
                ctx.intent = SupportIntent(res_data.intent) if res_data.intent in valid_intents else SupportIntent.PRODUCT_QUERY
                ctx.ui_component = res_data.ui_component
                return True 
            
            logger.warning(f"⚠️ [ConsultantHandler] AI returned invalid data: {type(res)}")
            return False 
            
        except Exception as e:
            logger.error(f"[ConsultantHandler] Sweep Failure: {e}")
            return False
