"""
Support Agent Operative — SUPPORT_NAME_CLIENT (Architect's Edition)
==================================================================
Elite V2.2: Zero-Hydration, Full Async I/O, 100% Static Typing.
"""
from __future__ import annotations

import asyncio
import json
import os
import logging
import re
import time
import uuid
from typing import Optional, cast, Union, Dict, Type, List, Tuple

from pydantic import BaseModel, Field, ConfigDict, JsonValue
from pydantic_ai import Agent, RunContext
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.commerce import ProductBase, Order
from backend.database.models.content import Category
from backend.database.models.system import SupportChatHistory
from backend.schemas.support import SupportIntent, SupportRequest, SupportResponse, SupportProductInfo
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.services.commerce.constants.support_config import support_cfg
from backend.services.event_bus import event_bus
from backend.services.xohi_memory import xohi_memory
from backend.utils.security import GeminiSecurity

logger = logging.getLogger("api-gateway")

class AgenticSupportResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    reply: str = Field(..., description="Văn bản phản hồi tự nhiên. Nếu khách muốn xem hình hoặc hỏi sản phẩm, hãy dùng PRODUCT_CARD.")
    intent: str = Field(..., description="MỘT trong các chuỗi sau: 'ORDER_STATUS', 'ESCALATE', 'POLICY_QUERY', 'PRICE_QUERY', 'PURCHASE', 'GENERAL_ADVICE', 'UNKNOWN'")
    ui_component: Optional[str] = Field(default=None, description="PRODUCT_CARD | POLICY_CARD | NONE")

class FastIntentResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    intent: str = Field(..., description="GREETING, POLICY, PRODUCT, ORDER, PURCHASE, OTHER")
    confidence: float = Field(default=1.0)
    quick_reply: Optional[str] = None

class MicroIntentResolver:
    """LAYER 0: Ultra-fast Regex/Heuristic Resolver (<10ms)."""
    @staticmethod
    def resolve(message: str, product_slug: Optional[str] = None) -> Optional[Tuple[SupportIntent, str]]:
        m = message.lower().strip()
        # 1. Specialized Greeting (Elite V2.2: Product-Driven)
        # Using containment check for better sensitivity (e.g., 'Chào bạn', 'Helen ơi')
        keywords = [k.strip().lower() for k in support_cfg.greeting_keywords]
        is_greeting = any(kw in m for kw in keywords)
        
        if product_slug == support_cfg.hong_son_slug:
            if is_greeting:
                reply = (
                    "Dạ Helen chào Anh/Chị! 🌸 Em thấy mình đang quan tâm đến liệu trình **Đặc trị Hôi nách Hồng Sơn**. "
                    "Đừng để vấn đề này làm mình mất tự tin thêm nữa ạ, hàng ngàn khách bên em đã lấy lại sự tự tin và thoải mái chỉ sau 1 liệu trình. "
                    "Anh/Chị bị tình trạng này lâu chưa, để em tư vấn liệu trình phù hợp nhất cho mình nhé?"
                )
                return SupportIntent.GENERAL_ADVICE, reply
            
            # 🚀 Elite V2.2: Hong Son Catch-All for any message that isn't a specific intent but on this page
            # This ensures we don't leak generic replies for ambiguous messages on the specialist page.
            # (Wait, we allow other intents like ORDER_STATUS to follow through below)

        # 2. Greetings (Elite V2.2: Config-driven)
        if is_greeting:
            return SupportIntent.GENERAL_ADVICE, support_cfg.default_greeting_reply
        # 3. Simple Order Status (ID pattern)
        if re.search(r"(đơn hàng|mã đơn|check đơn|đơn).*?([a-f0-9-]{8,})", m):
            return SupportIntent.ORDER_STATUS, "Helen đang kiểm tra mã đơn hàng của Quý khách, chờ em một chút nhé... 🔍"
        # 4. Pathology Direct Intent (Elite V2.2: Ultra-Fast Redirect)
        if any(kw in m for kw in ["hôi nách", "mồ hôi", "thâm nách", "tự tin", "hôi chân", "mồ hôi tay"]):
            return SupportIntent.PRODUCT_QUERY, "Dạ vấn đề này bên em có liệu trình chuyên biệt cực kỳ hiệu quả ạ. Quý khách đợi em tư vấn kỹ hơn nhé! 🌸"
        return None

class NeuralDNA(BaseModel):
    """Elite V2.2: Customer Personality & Segment DNA."""
    model_config = ConfigDict(strict=True)
    segment: str = Field(default="NEW", description="VIP | NEW | CHURN")
    vibe: str = Field(default="PROFESSIONAL", description="WARM | PROFESSIONAL")
    purchase_count: int = 0
    total_spent: float = 0.0
    last_hook: Optional[str] = None

class SupportAgentDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession

# ══════════════════════════════════════════════════════════════
# PYDANTIC AI AGENTS — Singleton (Elite V2.2 Standards)
# ══════════════════════════════════════════════════════════════
_support_ai_agent: Agent[SupportAgentDeps, AgenticSupportResponse] = Agent(
    output_type=AgenticSupportResponse,
    retries=1, 
)

_fast_intent_agent: Agent[None, FastIntentResponse] = Agent(
    output_type=FastIntentResponse,
    system_prompt=(
        "You are Helen's Fast Intent Classifier. Classify user message into: "
        "GREETING, POLICY, PRODUCT, ORDER, PURCHASE, OTHER. "
        "If it's a simple greeting, provide a friendly quick_reply in Vietnamese. "
        "Confidence must be 0.0 to 1.0."
    )
)

@_support_ai_agent.tool
async def get_knowledge_index(ctx: RunContext[SupportAgentDeps]) -> str:
    """LAYER 1: Tra cứu mục lục kiến thức Helen Brain."""
    from backend.database.repositories import SupportKnowledgeRepository
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    repo = SupportKnowledgeRepository(session=ctx.deps.db)
    service = SupportKnowledgeService(repo=repo)
    return await service.get_knowledge_index(ctx.deps.db)

@_support_ai_agent.tool
async def fetch_topic_details(ctx: RunContext[SupportAgentDeps], topic_id: str) -> str:
    """LAYER 2: Tra cứu thông tin chi tiết của một chủ đề."""
    from backend.database.repositories import SupportKnowledgeRepository
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    repo = SupportKnowledgeRepository(session=ctx.deps.db)
    service = SupportKnowledgeService(repo=repo)
    return await service.fetch_topic_details(ctx.deps.db, topic_id)

@_support_ai_agent.tool
async def search_knowledge_base(ctx: RunContext[SupportAgentDeps], query: str) -> str:
    """LAYER 3: Tìm kiếm mờ trong toàn bộ kho tri thức."""
    from backend.database.repositories import SupportKnowledgeRepository
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    repo = SupportKnowledgeRepository(session=ctx.deps.db)
    service = SupportKnowledgeService(repo=repo)
    return await service.search_relevant_knowledge(ctx.deps.db, query)

async def _fetch_product_context(db: AsyncSession, slug: Optional[str]) -> Tuple[str, Optional[SupportProductInfo]]:
    """Fetch product info via SQLAlchemy 2.0 Scalar projection."""
    if not slug: return "", None
    try:
        stmt = (
            select(ProductBase)
            .where(and_(ProductBase.slug == slug, ProductBase.deleted_at.is_(None), ProductBase.status == "ACTIVE"))
        )
        res = await db.execute(stmt)
        p = res.scalar_one_or_none()
        if not p: return "", None
        img_url = p.images[0] if p.images and len(p.images) > 0 else None
        p_info = SupportProductInfo(
            id=str(p.id), 
            name=p.name, 
            price=float(p.price or 0), 
            price_display=f"{int(p.discount_price or p.price or 0):,}đ".replace(",", "."), 
            slug=slug or "",
            image_url=img_url
        )
        ctx = f"[SẢN PHẨM HIỆN TẠI]\nTên: {p.name}\nMô tả: {p.short_description}\nGiá niêm yết: {p.price} VND\n"
        if p.discount_price: ctx += f"Giá khuyến mãi: {p.discount_price} VND\n"
        return ctx, p_info
    except Exception as e:
        logger.warning("[SupportAgent] Context sweep failure: %s", e)
        return "", None

def _sanitize_response(text: str) -> str:
    """Surgical leak prevention (Elite V2.2)."""
    clean = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
    clean = re.sub(r"/\w+/\w+/\w+", "[REDACTED]", clean)
    return clean.strip()

class SupportAgentOperative(BaseAgentOperative):
    """Refined Architect-level Operative."""
    agent_id_class = "support_agent"

    def __init__(self, agent_id: str = "support_agent"):
        super().__init__(agent_id=agent_id)

    def get_schema(self) -> Optional[Type[BaseModel]]:
        return SupportRequest

    async def _save_history(self, db: AsyncSession, session_id: str, user_msg: str, assistant_reply: str, intent: SupportIntent, product_slug: Optional[str], customer_name: Optional[str] = None, customer_phone: Optional[str] = None) -> None:
        """Encrypted transactional history persistence."""
        try:
            enc_user_msg = GeminiSecurity.encrypt(user_msg)
            enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)
            msg_user = SupportChatHistory(session_id=session_id, role="user", content=enc_user_msg, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            msg_ai = SupportChatHistory(session_id=session_id, role="assistant", content=enc_assistant_reply, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            db.add_all([msg_user, msg_ai])
            await db.flush()
            
            # 🚀 Elite V2.2: Proactive Follow-up (Feedback Loop)
            # Schedule a reminder in 1 hour if the user doesn't respond.
            # Using 'high' queue for support priority. 
            try:
                from arq import create_pool
                from backend.infra.arq_config import get_redis_settings
                redis = await create_pool(get_redis_settings())
                await redis.enqueue_job(
                    "helen_follow_up_job",
                    session_id=session_id,
                    _defer_by=3600, # 1 hour (3600s)
                    _job_id=f"followup:{session_id}:{int(time.time())}", # Avoid colliding with same-second jobs
                    _queue_name="high"
                )
                await redis.close()
            except Exception as arqe:
                logger.warning("[SupportAgent] Follow-up scheduling failed: %s", arqe)
        except Exception as exc:
            logger.warning("[SupportAgent] Saving failed: %s", exc)

    async def _fetch_chat_context(self, db: AsyncSession, session_id: str) -> str:
        """Context-window hydration (Elite V2.2)."""
        try:
            stmt = select(SupportChatHistory).where(SupportChatHistory.session_id == session_id).order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id)).limit(4)
            history_rows = (await db.execute(stmt)).scalars().all()
            if not history_rows: return ""
            h_parts = []
            for r in reversed(history_rows):
                h_content = GeminiSecurity.decrypt(r.content) if r.content else ""
                h_role = "Khách" if r.role == "user" else "Helen"
                h_parts.append(f"{h_role}: {h_content}")
            return "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n"
        except: return ""

    def _calculate_delivery_time(self, address: str, shipping_days: Optional[str] = None) -> str:
        """Elite V2.5: Logistics-Integrated Shipping Estimator."""
        # 1. Use high-fidelity data from Resolver if available
        if shipping_days: return shipping_days
        
        # 2. Fallback to heuristic keyword matching (R0.3 Heritage)
        if not address: return "2-3 ngày"
        addr: str = address.lower()
        hcm_keys = ["hồ chí minh", "tp.hcm", "hcm", "sài gòn", "phú lâm", "quận 1", "quận 2", "quận 3", "quận 4", "quận 5", "quận 6", "quận 7", "quận 8", "quận 9", "quận 10", "quận 11", "quận 12", "bình tân", "bình thạnh", "gò vấp", "phú nhuận", "tân bình", "tân phú", "thủ đức", "hóc môn", "củ chi", "nhà bè", "bình chánh", "cần giờ"]
        if any(key in addr for key in hcm_keys): return "1 ngày"
        
        south_keys = ["bình phước", "bình dương", "đồng nai", "tây ninh", "vũng tàu", "long an", "tiền giang", "vĩnh long", "bến tre", "kiên giang", "cần thơ", "hậu giang", "trà vinh", "sóc trăng", "bạc liêu", "cà mau"]
        if any(key in addr for key in south_keys): return "1-2 ngày"
        
        return "3-5 ngày"

    async def _fetch_neural_dna(self, db: AsyncSession, session_id: str) -> NeuralDNA:
        """Hydrate Neural DNA from memory and DB context."""
        try:
            # 1. Try xohi_memory first
            mem = await xohi_memory.get_user_context(session_id)
            if mem and "dna" in mem:
                return NeuralDNA.model_validate(mem["dna"])
            
            # 2. Hard-check DB if not in memory
            stmt = select(Order).where(Order.session_id == session_id).order_by(desc(Order.created_at))
            orders = (await db.execute(stmt)).scalars().all()
            
            dna = NeuralDNA(
                segment="VIP" if len(orders) >= 5 else ("NEW" if not orders else "REGULAR"),
                vibe="WARM" if len(orders) >= 3 else "PROFESSIONAL",
                purchase_count=len(orders),
                total_spent=sum(float(o.total_amount or 0) for o in orders)
            )
            # Sync back to memory
            await xohi_memory.set_user_context(session_id, {"dna": dna.model_dump()})
            return dna
        except Exception as e:
            logger.warning("[SupportAgent] DNA fetch failed: %s", e)
            return NeuralDNA()

    async def _build_prompt_directive(self, product_ctx: str, history_text: str = "", lead_metadata: Optional[Dict[str, JsonValue]] = None, dna: Optional[NeuralDNA] = None, product_slug: Optional[str] = None) -> str:
        """Strategic Sales Prompt Construction."""
        res = await xohi_memory.client.get("support:agent:system_prompt")
        agentic_directive = res.decode("utf-8") if isinstance(res, bytes) else res

        if not agentic_directive:
            try:
                if os.path.exists(support_cfg.prompt_template_path):
                    def _read_file() -> str:
                        with open(support_cfg.prompt_template_path, "r", encoding="utf-8") as f:
                            return f.read()
                    agentic_directive = await asyncio.to_thread(_read_file)
                else:
                    agentic_directive = support_cfg.system_directive
            except Exception as e:
                logger.warning("[SupportAgent] Prompt template read failure: %s", e)
                agentic_directive = support_cfg.system_directive

        # 🚀 PERSONALITY & VIBE (Neural DNA)
        vibe_str = ""
        if dna:
            if dna.segment == "VIP":
                vibe_str = (
                    "\n[NEURAL VIBE: VIP WARM]\n"
                    "- Xưng hô: 'Helen' hoặc 'Dạ Helen thân chào Quý khách'.\n"
                    "- Phong cách: Cực kỳ thân mật, thấu hiểu, ưu tiên nhắc về các đặc quyền VIP.\n"
                    f"- Thông số: Khách đã mua {dna.purchase_count} lần, tổng chi tiêu {dna.total_spent:,.0f}đ.\n"
                )
            elif dna.segment == "CHURN":
                vibe_str = (
                    "\n[NEURAL VIBE: SAVE HOOK]\n"
                    "- Phong cách: Chủ động lôi kéo, dùng 'Save Hook' (giảm 10%) nếu khách có vẻ do dự.\n"
                )
            else:
                vibe_str = (
                    "\n[NEURAL VIBE: PROFESSIONAL NEWBIE]\n"
                    "- Xưng hô: 'Dạ Helen chào quý khách'.\n"
                    "- Phong cách: Chuẩn mực, tập trung giải thích giá trị sản phẩm và cam kết chất lượng.\n"
                )

        # 🚀 VISUAL CAPABILITY ENFORCEMENT
        visual_rules = (
            "\n[VISUAL CAPABILITIES: SHOW, DON'T JUST TELL]\n"
            "- Bạn CÓ KHẢ NĂNG hiển thị hình ảnh sản phẩm thông qua PRODUCT_CARD.\n"
            "- Khi user yêu cầu: 'cho xem hình', 'mẫu thế nào', 'gửi ảnh'... BẮT BUỘC đặt ui_component='PRODUCT_CARD'.\n"
            "- Đừng bao giờ nói: 'Tôi không thể hiển thị hình ảnh'.\n"
        )

        # 🚀 SPECIALIST PERSONA (Elite V2.2: Product-Specific)
        specialist_directive = ""
        if product_slug == support_cfg.hong_son_slug:
            specialist_directive = (
                "\n[SPECIALIST: HÔI NÁCH HỒNG SƠN - VUA TRÙM ĐẶC TRỊ]\n"
                "- Bối cảnh: Bạn đang ở trang đặc trị sản phẩm chiến lược của hệ thống.\n"
                "- Vai trò: Chuyên gia tư vấn về tình trạng mùi cơ thể. Luôn tế nhị, thấu hiểu. Giải thích cơ chế khoa học: 'Thấm sâu vào lỗ chân lông, trung hòa axit béo, se khít lỗ chân lông để vùng da luôn khô thoáng'.\n"
                "- THỊ GIÁC: Chủ động hiển thị PRODUCT_CARD ngay trong câu chào hoặc khi khách tò mò để tăng độ tin cậy.\n"
                "- TUYỆT ĐỐI KHÔNG DÙNG CÁC TỪ: 'Gia truyền', 'Dứt điểm', 'Bác sĩ khuyên dùng'.\n"
                "- CHÍNH SÁCH: Nhấn mạnh vào hiệu quả thực tế từ người dùng và chất lượng sản phẩm được kiểm định. KHÔNG hứa hẹn 'hoàn tiền' hoặc 'dụ dỗ' thái quá.\n"
                "- Kỷ luật: CHỈ tư vấn và bán DUY NHẤT sản phẩm Hồng Sơn khi ở trang này. Nếu khách hỏi sản phẩm khác, hãy khéo léo từ chối và nhắc lại giá trị của Hồng Sơn đối với tình trạng của họ.\n"
                "- Martial Combo Rules for Hong Son:\n"
                "  + 1 Lọ: 249k (Dùng thử, trải nghiệm độ khô thoáng).\n"
                "  + 3 Lọ (Mua 2 tặng 1): 498k. LIỆU TRÌNH CHUẨN ĐỂ ĐẠT HIỆU QUẢ TỐI ƯU.\n"
                "  + 6 Lọ (Mua 4 tặng 2): 996k. Liệu trình cho cả gia đình hoặc trường hợp ra mồ hôi quá nhiều.\n"
            )

        # 🚀 MARTIAL COMBO & MEMORY PROTOCOL (Elite V2.2)
        rules = (
            "\n[MEMORY PROTOCOL: 3-LAYER]\n"
            "1. LUÔN tra cứu Layer 1 (get_knowledge_index) để biết có chủ đề liên quan hông.\n"
            "2. Nếu thấy ID phù hợp, BẮT BUỘC dùng fetch_topic_details để lấy tri thức chuyên sâu.\n"
            "3. Chỉ dùng kiến thức được hệ thống phê duyệt (Layer 2) để trả lời về Cam kết, So sánh, HDSD.\n"
            "\n[SALES PROTOCOL: MARTIAL COMBO]\n"
            "1. Liệu trình 1 Lọ: 249k (Dùng thử).\n"
            "2. Liệu trình 3 Lọ (Dứt điểm): Chỉ 498k (Mua 2 tặng 1) - Tiết kiệm 249k. LỰA CHỌN TỐI ƯU NHẤT!\n"
            "3. Liệu trình 6 Lọ (Cả gia đình): Chỉ 996k (Mua 4 tặng 2). Tiết kiệm 498k.\n"
            "4. Số lượng > 6: Block chốt đơn tự động, Helen sẽ báo giá sỉ riêng cực ưu đãi.\n"
        )
        
        meta_str = ""
        if lead_metadata:
            meta_str = "\n[SYSTEM ALERT]\n"
            if lead_metadata.get("is_new_customer"): meta_str += "- Khách hàng MỚI.\n"
            if lead_metadata.get("needs_price_quote"): meta_str += "- CẢNH BÁO: Số lượng sỉ (>6), KHÔNG báo giá tự động.\n"

        # 🚀 SYSTEM FOLLOW-UP PROTOCOL (Elite V2.2)
        follow_up_meta = ""
        # If the incoming message is a system trigger, inject specific sales psychology
        # We also check history_text just in case it was injected there
        if "[SYSTEM_FOLLOW_UP_TRIGGER]" in (product_ctx + history_text):
             follow_up_meta = (
                 "\n[CRITICAL: PROACTIVE FOLLOW-UP]\n"
                 "- Helen đang chủ động nhắn tin hỏi thăm khách sau 1 giờ im lặng.\n"
                 "- Hãy dùng tông giọng quan tâm, chuyên nghiệp kiểu: 'Dạ, có phải Anh/Chị còn đang băn khoăn về liệu trình Hồng Sơn của bên em không ạ?'\n"
                 "- Nhấn mạnh lại cam kết dứt điểm và Helen sẵn sàng hỗ trợ Quý khách 24/7.\n"
             )

        return f"{agentic_directive}\n{vibe_str}\n{visual_rules}\n{specialist_directive}\n{rules}\n{meta_str}\n{follow_up_meta}\n{history_text}\n--- PRODUCT ---\n{product_ctx}\n"

    async def process_brain_logic(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        """Final Refined Async Processor."""
        t0 = time.monotonic()
        session_id = request.session_id or str(uuid.uuid4())
        from backend.services.commerce.logic.lead_extractor import lead_extractor
        lead_data = await lead_extractor.extract_and_convert(db, request.message, session_id, current_product_slug=request.product_slug)
        
        # 🔗 Deterministic Path (Order Success)
        if lead_data and getattr(lead_data, "processed_order_id", None):
            order_id: str = str(lead_data.processed_order_id)
            order_obj = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
            if order_obj:
                total_qty: int = 0
                if isinstance(order_obj.items, list):
                    for it in order_obj.items:
                        if isinstance(it, dict): total_qty += int(it.get("quantity", 1))
                
                formatted_price: str = "{:,.0f}".format(float(order_obj.total_amount or 0)).replace(",", ".")
                delivery_info: str = self._calculate_delivery_time(order_obj.customer_address or "", getattr(lead_data, "shipping_days", None))
                
                reply = (
                    f"Dạ Helen xin cảm ơn quý khách! 🌸\nĐơn hàng thành công:\n- Mã đơn: **{order_id[-8:].upper()}**\n"
                    f"- Số sản phẩm: {total_qty} lọ/combo\n- Tổng tiền: **{formatted_price}đ** (đã free ship)\n"
                    f"- Nhận hàng: **{delivery_info}**\n\n[🔍 KIỂM TRA ĐƠN HÀNG](https://smartshop.test/account/orders/{order_id})"
                )
                await self._save_history(db, session_id, request.message, reply, SupportIntent.PURCHASE, request.product_slug, request.customer_name, lead_data.customer_phone)
                await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
                return SupportResponse(ok=True, reply=reply, intent=SupportIntent.PURCHASE, session_id=session_id, status="DONE")

        # 🔗 Probabilistic Path (AI Conversation)
        lead_meta = {
            "is_new_customer": lead_data.is_new_customer,
            "needs_price_quote": getattr(lead_data, "needs_price_quote", False),
            "address_status": getattr(lead_data, "address_status", "UNKNOWN")
        } if lead_data else None

        ctx_text, p_info = await _fetch_product_context(db, request.product_slug)
        hist_text = await self._fetch_chat_context(db, session_id)
        dna = await self._fetch_neural_dna(db, session_id)
        
        # 🚀 GHOST STREAMING: Start "Inner Monologue"
        await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Đang phân tích tri thức Helen..."})
        
        prompt = await self._build_prompt_directive(ctx_text, hist_text, lead_metadata=lead_meta, dna=dna, product_slug=request.product_slug)
        
        try:
            # 🚀 GHOST STREAMING: Neural Search
            await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": f"Đang tra cứu DNA {dna.segment}..."})
            
            res = await trinity_bridge.run(_support_ai_agent, request.message, role=support_cfg.model_role, system_prompt=prompt, deps=SupportAgentDeps(db=db), timeout=15.0)
            data: AgenticSupportResponse = res.output # type: ignore
            raw_reply = data.reply or "Dạ Helen đã ghi nhận thông tin ạ!"
            raw_intent = data.intent or "UNKNOWN"
            ui_component = data.ui_component
            
            # 🚀 GHOST STREAMING: Finalizing
            await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Chuẩn bị phản hồi chuyên nghiệp..."})
            
        except Exception as e:
            logger.error("[SupportAgent] Sweep Failure: %s", e)
            raw_reply = "Dạ hệ thống Helen đang bảo trì nhẹ một xíu, Quý khách đợi em nhé! 🌸"
            raw_intent = "UNKNOWN"
            ui_component = None

        safe_reply = _sanitize_response(raw_reply)
        
        # Hydrate ui_metadata if component is PRODUCT_CARD
        ui_meta: Optional[Dict[str, JsonValue]] = None
        if ui_component == "PRODUCT_CARD" and p_info:
            ui_meta = {"type": "PRODUCT_CARD", "data": p_info.model_dump()}
        
        await self._save_history(db, session_id, request.message, safe_reply, SupportIntent(raw_intent) if raw_intent in [i.value for i in SupportIntent] else SupportIntent.UNKNOWN, request.product_slug, request.customer_name, request.customer_phone)
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
        
        return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent(raw_intent), session_id=session_id, product_info=p_info, status="DONE", ui_metadata=ui_meta)

    async def chat(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        """
        Viral Hook Engine: Layered Entry Protocol.
        L0: Micro-Heuristics (<10ms)
        L1: Fast-Path LLM (<200ms)
        L2: Deep Brain (Background Task)
        """
        session_id = request.session_id or str(uuid.uuid4())
        
        # 🚀 LAYER 0: Micro-Heuristics (Regex/Exact)
        micro_res = MicroIntentResolver.resolve(request.message, product_slug=request.product_slug)
        if micro_res:
            intent, reply = micro_res
            await self._save_history(db, session_id, request.message, reply, intent, request.product_slug)
            return SupportResponse(ok=True, reply=reply, intent=intent, session_id=session_id, status="DONE")

        # 🚀 LAYER 1: Fast-Path LLM (Intent Classification)
        # Elite V2.2 Lockdown: Skip Fast-Path for Strategic Specialist Products
        if request.product_slug == support_cfg.hong_son_slug:
            logger.info("[SupportAgent] Lockdown: Bypassing Fast-Path for Hong Son Specialist.")
        else:
            try:
                # We use a very short timeout for Fast-Path to ensure Ultra-Fast UX
                # Elite V2.2: Specify role='fast' to use lightweight models
                fast_res = await trinity_bridge.run(_fast_intent_agent, request.message, role="fast", timeout=2.0)
                f_data: FastIntentResponse = fast_res.output # type: ignore
                
                if f_data.intent == "GREETING" and f_data.quick_reply:
                    await self._save_history(db, session_id, request.message, f_data.quick_reply, SupportIntent.GENERAL_ADVICE, request.product_slug)
                    return SupportResponse(ok=True, reply=f_data.quick_reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")
            except Exception as e:
                logger.warning("[SupportAgent] Fast-Path Bypass: %s", e)

        # 🚀 LAYER 2: Deep Brain (Complex Logic via Arq)
        task_id = await self.enqueue_chat(request_data=request.model_dump(), session_id=session_id)
        return SupportResponse(ok=True, reply="Helen đang xử lý...", intent=SupportIntent.UNKNOWN, session_id=session_id, task_id=task_id, status="PROCESSING")

support_agent = SupportAgentOperative()
