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
from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER
from backend.database.alchemy_config import alchemy_config
from backend.services.commerce.constants.support_config import support_cfg
from backend.services.event_bus import event_bus
from backend.services.xohi_memory import xohi_memory
from backend.utils.security import GeminiSecurity

from backend.services.commerce.operatives.handlers.base import NeuralDNA, SupportContext
from backend.services.commerce.operatives.router import SupportRouter

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
            select(
                ProductBase.id,
                ProductBase.name,
                ProductBase.price,
                ProductBase.discount_price,
                ProductBase.slug,
                ProductBase.stock,
                ProductBase.short_description,
                ProductBase.images
            )
            .where(and_(ProductBase.slug == slug, ProductBase.deleted_at.is_(None), ProductBase.status == "ACTIVE"))
        )
        res = await db.execute(stmt)
        p_row = res.first()
        if not p_row: return "", None
        img_url = p_row.images[0] if p_row.images and len(p_row.images) > 0 else None
        p_info = SupportProductInfo(
            id=str(p_row.id), 
            name=p_row.name, 
            price=float(p_row.price or 0), 
            price_display=f"{int(p_row.discount_price or p_row.price or 0):,}đ".replace(",", "."), 
            slug=p_row.slug or "",
            image_url=img_url,
            stock=p_row.stock
        )
        ctx = f"[SẢN PHẨM HIỆN TẠI]\nTên: {p_row.name}\nMô tả: {p_row.short_description}\nGiá niêm yết: {p_row.price} VND\n"
        if p_row.discount_price: ctx += f"Giá khuyến mãi: {p_row.discount_price} VND\n"
        ctx += f"Tồn kho thực tế: {p_row.stock or 0} sản phẩm\n"
        return ctx, p_info
    except Exception as e:
        logger.warning("[SupportAgent] Context sweep failure: %s", e)
        return "", None

def _sanitize_response(text: str) -> str:
    """Surgical leak prevention (Elite V2.2)."""
    # 1. Hide AI thought tags
    clean = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
    # 2. Redact internal paths
    clean = re.sub(r"/\w+/\w+/\w+", "[REDACTED_PATH]", clean)
    # 3. Privacy Guard: Mask Phone Numbers (Vietnamese format)
    clean = re.sub(r"(0|84|(\+84))(\d{2,3})[\s\.\-]?(\d{3})[\s\.\-]?(\d{3,4})", r"\1\3****\5", clean)
    return clean.strip()

class SupportAgentOperative(BaseAgentOperative):
    """Refined Architect-level Operative."""
    agent_id_class = "support_agent"

    def __init__(self, agent_id: str = "support_agent"):
        super().__init__(agent_id=agent_id)
        self.router = SupportRouter()
        self._arq_pool = None

    async def _get_arq_pool(self):
        if self._arq_pool is None:
            from arq import create_pool
            from backend.infra.arq_config import get_redis_settings
            self._arq_pool = await create_pool(get_redis_settings())
        return self._arq_pool

    def get_schema(self) -> Optional[Type[BaseModel]]:
        return SupportRequest

    async def _save_history(self, db: AsyncSession, session_id: str, user_msg: str, assistant_reply: str, intent: SupportIntent, product_slug: Optional[str], customer_name: Optional[str] = None, customer_phone: Optional[str] = None) -> None:
        """Encrypted transactional history persistence."""
        try:
            # Shield internal trigger from history
            if user_msg != HELEN_FOLLOW_UP_TRIGGER:
                enc_user_msg = GeminiSecurity.encrypt(user_msg)
                msg_user = SupportChatHistory(session_id=session_id, role="user", content=enc_user_msg, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
                db.add(msg_user)

            enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)
            msg_ai = SupportChatHistory(session_id=session_id, role="assistant", content=enc_assistant_reply, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            db.add(msg_ai)
            await db.flush()
            logger.info("[SupportAgent] Persisted chat segment for SID: %s", session_id)
            
            # 🚀 Elite V2.2: Proactive Follow-up (Feedback Loop)
            # Schedule a reminder in 1 hour if the user doesn't respond.
            # Only if this is a real user message (not a system trigger)
            if user_msg != HELEN_FOLLOW_UP_TRIGGER:
                try:
                    redis = await self._get_arq_pool()
                    await redis.enqueue_job(
                        "helen_follow_up_job",
                        session_id=session_id,
                        _defer_by=3600, # 1 hour (3600s)
                        _job_id=f"followup:{session_id}:{int(time.time())}", 
                        _queue_name="high"
                    )
                except Exception as arqe:
                    logger.warning("[SupportAgent] Follow-up scheduling failed: %s", arqe)
        except Exception as exc:
            logger.warning("[SupportAgent] Saving failed: %s", exc)

    async def _fetch_chat_context(self, db: AsyncSession, session_id: str) -> str:
        """Context-window hydration (Elite V2.2). Enhanced to 10 turns with character clipping."""
        try:
            stmt = select(SupportChatHistory).where(SupportChatHistory.session_id == session_id).order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id)).limit(10)
            history_rows = (await db.execute(stmt)).scalars().all()
            if not history_rows: return ""
            h_parts = []
            total_chars = 0
            MAX_TOTAL_CHARS = 5000 # Safety cap for context window

            for r in reversed(history_rows):
                h_content = GeminiSecurity.decrypt(r.content or "")
                if h_content == HELEN_FOLLOW_UP_TRIGGER:
                    continue # Elite V2.2: Shield internal triggers
                
                # Làm sạch dữ liệu log chat (trunc history) để tránh bùng nổ context
                # Giới hạn mỗi tin nhắn 300 ký tự
                if len(h_content) > 300:
                    h_content = h_content[:300] + "... [TRUNCATED_HISTORY]"
                
                # Global Context Guard
                if total_chars + len(h_content) > MAX_TOTAL_CHARS:
                    break

                h_role = "Khách" if r.role == "user" else "Helen"
                h_parts.append(f"{h_role}: {h_content}")
                total_chars += len(h_content)

            return "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n" if h_parts else ""
        except: return ""

    async def _fetch_neural_dna(self, db: AsyncSession, session_id: str, lead_phone: Optional[str] = None) -> NeuralDNA:
        """Hydrate Neural DNA from memory or Order History (Elite V2.2: Lead-driven)."""
        try:
            mem = await xohi_memory.get_user_context(session_id)
            if mem and "dna" in mem:
                return NeuralDNA.model_validate(mem["dna"])
            
            # Elite V2.2: If we have a phone, we can look up order history to determine seniority.
            total_spent = 0.0
            order_count = 0
            if lead_phone:
                from backend.database.models.commerce import Order
                stmt = select(Order).where(and_(Order.customer_phone == lead_phone, Order.status == "COMPLETED"))
                orders = (await db.execute(stmt)).scalars().all()
                order_count = len(orders)
                total_spent = sum(float(o.total_amount or 0) for o in orders)

            dna = NeuralDNA(
                segment="VIP" if order_count >= 3 else ("REGULAR" if order_count >= 1 else "NEW"),
                vibe="WARM" if order_count >= 1 else "PROFESSIONAL",
                purchase_count=order_count,
                total_spent=total_spent
            )
            await xohi_memory.set_user_context(session_id, {"dna": dna.model_dump()})
            return dna
        except Exception as e:
            logger.warning("[SupportAgent] DNA fetch failed: %s", e)
            return NeuralDNA()

    async def process_brain_logic(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        """Architecture V2.5: Orchestrated Specialist Pipeline."""
        session_id = request.session_id or str(uuid.uuid4())
        
        # 🚀 1. HYDRATE CONTEXT (Zero-Leak Hydration)
        await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": "Đang đồng bộ DNA Helen..."})
        
        ctx_text, p_info = await _fetch_product_context(db, request.product_slug)
        hist_text = await self._fetch_chat_context(db, session_id)
        dna = await self._fetch_neural_dna(db, session_id)
        
        logger.info(f"🧠 [SupportAgent] Processing Brain Logic for Session: {session_id}")
        logger.debug(f"📜 [SupportAgent] History Window: {hist_text[:100]}...")
        
        # 🚀 1.0.1: Layer 1 Memory (Knowledge Map) - Elite V2.2 Protocol
        try:
            from backend.database.repositories import SupportKnowledgeRepository
            from backend.services.commerce.support_knowledge import SupportKnowledgeService
            repo = SupportKnowledgeRepository(session=db)
            kb_service = SupportKnowledgeService(repo=repo)
            kb_index = await kb_service.get_knowledge_index(db)
        except Exception as kbe:
            logger.warning("[SupportAgent] Knowledge Index fetch failed: %s", kbe)
            kb_index = ""

        # 🚀 1.1: Fetch Integration Config (Elite V2.2)
        zalo_on = await xohi_memory.client.get("system:zalo_enabled") != "0"
        messenger_on = await xohi_memory.client.get("system:messenger_enabled") != "0"

        # 🚀 1.2: Elite FOMO Sync
        from backend.services.commerce.logic.fomo_service import fomo_service
        active_visitors = await fomo_service.get_active_visitors_count()

        ctx = SupportContext(
            db=db,
            request=request,
            session_id=session_id,
            dna=dna,
            product_ctx=ctx_text,
            history_text=hist_text,
            knowledge_index=kb_index,
            p_info=p_info,
            zalo_enabled=zalo_on,
            messenger_enabled=messenger_on,
            active_visitors=active_visitors,
            product_stock=p_info.stock if p_info else 0
        )
        
        # 🚀 2. EXECUTE PIPELINE (The Specialists)
        await event_bus.emit("SUPPORT_THOUGHT", {"session_id": session_id, "think": f"Đang điều phối chuyên gia {dna.segment}..."})
        
        ctx = await self.router.process(ctx)
        
        # 🚀 3. POST-PROCESSING (Verification & Finalization)
        # We join all collected replies into one natural message
        final_reply = " ".join(ctx.replies).strip() if ctx.replies else "[fallback] Dạ Helen xin lỗi, hiện tại em đang bận xử lý dữ liệu một chút. Anh/Chị vui lòng nhập câu hỏi rõ hơn hoặc chờ em giây lát nhé! 🌸"
        safe_reply = _sanitize_response(final_reply) or "[fallback] Dạ em đang kết nối lại, Anh/Chị thông cảm nhé!"
        
        # Final Intent and Component Logic
        final_intent = ctx.intent or SupportIntent.UNKNOWN
        
        # Hydrate ui_metadata if component is PRODUCT_CARD
        if ctx.ui_component == "PRODUCT_CARD" and p_info:
            ctx.ui_metadata = {"type": "PRODUCT_CARD", "data": p_info.model_dump()}

        # 🚀 4. PERSISTENCE (Atomic Commit)
        await self._save_history(
            db, session_id, request.message, safe_reply, final_intent, 
            request.product_slug, request.customer_name, 
            ctx.lead_data.customer_phone if ctx.lead_data else None
        )
        # 🚀 Elite V2.2: Presence Tracking (Heartbeat)
        # Mark user as online for 2 minutes (120s)
        try:
            await xohi_memory.client.set(f"support:presence:{session_id}", "1", ex=120)
        except Exception as pe:
            logger.warning("[SupportAgent] Presence update failed: %s", pe)

        await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
        
        # 🚀 Elite V2.2: Ensure data is flushed for other agents to see
        await db.flush()
        
        return SupportResponse(
            ok=True, 
            reply=safe_reply, 
            intent=final_intent, 
            session_id=session_id, 
            product_info=p_info, 
            status="DONE", 
            ui_metadata=ctx.ui_metadata,
            processed_order_id=ctx.processed_order_id
        )

    async def chat(self, request: Union[SupportRequest, dict], **kwargs: object) -> SupportResponse:
        """
        Elite V2.5: Entry Protocol.
        Supports both direct API (SupportRequest) and Worker calls (dict).
        """
        # 0. Normalize Request & DB Session
        if isinstance(request, dict):
            request = SupportRequest.model_validate(request)
            
        db = cast(Optional[AsyncSession], kwargs.get("db"))
        if not db:
            # Lifecycle: Worker Context — Create standalone session
            session_maker = alchemy_config.create_session_maker()
            async with session_maker() as standalone_db:
                res = await self._chat_internal(request, standalone_db)
                await standalone_db.commit()
                logger.info("[SupportAgent] Worker commit successful for SID: %s", request.session_id)
                return res
        
        return await self._chat_internal(request, db)

    async def _chat_internal(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        """Internal dispatch logic with Elite V2.2 Inhibition Guards."""
        session_id = request.session_id or str(uuid.uuid4())

        # 🚀 Elite V2.2: Inhibition Guards (Handover & Global Control)
        # 1. Global Switch
        helen_on = await xohi_memory.client.get("system:helen_enabled")
        if helen_on == "0":
            return SupportResponse(
                ok=False, 
                reply="Hệ thống tư vấn AI hiện đang bảo trì. Vui lòng để lại lời nhắn cho dược sĩ ạ.", 
                intent=SupportIntent.UNKNOWN, 
                session_id=session_id, 
                status="FAILED"
            )

        # 2. Staff Takeover (Inverse Logic: 0 = Human Active / AI Blocked)
        takeover_val = await xohi_memory.client.get(f"support:takeover:{session_id}")
        if takeover_val == "0":
            logger.info("[SupportAgent] Helen inhibited for SID: %s (Human Takeover)", session_id)
            return SupportResponse(
                ok=True, 
                reply="Dược sĩ đang trực tiếp hỗ trợ sếp. Vui lòng đợi trong giây lát ạ.", 
                intent=SupportIntent.UNKNOWN, 
                session_id=session_id, 
                status="DONE"
            )
        
        # 🚀 FAST-PATH (Intent Classification Only)
        logger.info("[SupportAgent] Entering Fast-Path classification for SID: %s", session_id)
        try:
            # Elite V2.2: Shield sensitive terms before fast-path classification
            masked_msg = await self._mask_sensitive_medical_terms(request.message)
            fast_res = await trinity_bridge.run(
                _fast_intent_agent, 
                masked_msg, 
                role=trinity_bridge.ROLE_FAST, 
                timeout=2.0,
                safety_none=True
            )
            f_data = cast(FastIntentResponse, fast_res) # Proper Elite V2.2 Typing
            logger.info("[SupportAgent] Fast-Path detected intent: %s for SID: %s", f_data.intent, session_id)
            
            if f_data.intent == "GREETING" and f_data.quick_reply:
                await self._save_history(
                    db, session_id, request.message, f_data.quick_reply, 
                    SupportIntent.GENERAL_ADVICE, request.product_slug,
                    request.customer_name, request.customer_phone
                )
                await db.flush()
                return SupportResponse(ok=True, reply=f_data.quick_reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")
        except Exception as e:
            logger.warning("[SupportAgent] Fast-Path Bypass: %s", e)

        # 🚀 L0.5: SYNCHRONOUS HEURISTIC FAST-PATH (Elite V2.5 — Race Condition Fix)
        # Handles INFO_ADDRESS / INFO_INGREDIENTS / INFO_HOTLINE INSTANTLY, no background task.
        # ROOT CAUSE FIX: Eliminates off-by-one SSE race condition when users send messages
        # faster than background tasks complete.
        _, p_info = await _fetch_product_context(db, request.product_slug)
        heuristic_res = await self._try_heuristic_sync(request, db, session_id, p_info)
        if heuristic_res:
            return heuristic_res

        # 🚀 DEEP BRAIN (Background Task) — for complex queries only
        logger.info("[SupportAgent] Falling back to Deep-Brain for SID: %s", session_id)
        task_id = await self.enqueue_chat(request_data=request.model_dump(), session_id=session_id)
        logger.info("[SupportAgent] Deep-Brain task enqueued: %s for SID: %s", task_id, session_id)
        return SupportResponse(ok=True, reply="Helen đang xử lý...", intent=SupportIntent.UNKNOWN, session_id=session_id, task_id=task_id, status="PROCESSING")

    async def _try_heuristic_sync(self, request: SupportRequest, db: AsyncSession, session_id: str, p_info: Optional[SupportProductInfo] = None) -> Optional[SupportResponse]:
        """
        Elite V3.0: Synchronous Heuristic Fast-Path.
        - INFO_ADDRESS / INFO_HOTLINE → đọc SystemSettings (Redis cache) — không cần LLM, < 100ms.
        - PRICE_QUERY → đọc p_info trực tiếp — không cần LLM, < 100ms.
        - INFO_INGREDIENTS / INFO_SHIPPING → fall-through đến Deep-Brain (context-dependent).
        - Xóa sự phụ thuộc sai vào bảng support_knowledge cho dữ liệu cấu trúc.
        """
        from backend.database.models.system import SupportKnowledgeCategory
        from backend.database import current_tenant_id
        import json as _json

        msg_norm = request.message.lower().strip()
        detected_category: Optional[SupportKnowledgeCategory] = None
        matched_kw: Optional[str] = None

        # Priority 1: INGREDIENTS — fall-through to Deep-Brain (sản phẩm nào? cần AI phân tích)
        kws_ing = ["thành phần", "chiết xuất", "gồm những gì", "làm từ gì", "thảo dược gì", "công thức", "thành phần thuốc", "chất gì", "có gì trong thuốc"]
        for kw in kws_ing:
            if kw in msg_norm:
                detected_category = SupportKnowledgeCategory.INFO_INGREDIENTS
                matched_kw = kw
                break

        # Priority 2: ADDRESS
        if not detected_category:
            kws_addr = ["địa chỉ", "ở đâu", "chi nhánh", "cửa hàng", "văn phòng", "trụ sở", "phòng khám", "showroom", "địa điểm", "chỗ nào"]
            for kw in kws_addr:
                if kw in msg_norm:
                    detected_category = SupportKnowledgeCategory.INFO_ADDRESS
                    matched_kw = kw
                    break

        # Priority 3: HOTLINE
        if not detected_category:
            kws_hot = ["điện thoại", "hotline", "số điện thoại", "liên hệ", "sốđt", "sdt", "website", "tư vấn qua đâu"]
            for kw in kws_hot:
                if kw in msg_norm:
                    detected_category = SupportKnowledgeCategory.INFO_HOTLINE
                    matched_kw = kw
                    break

        # Priority 4: PRICE QUERY (Ultra-Fast)
        if not detected_category:
            kws_price = ["giá", "bao nhiêu", "nhiêu tiền", "nhiêu", "rổ giá", "giá cả"]
            for kw in kws_price:
                if kw in msg_norm:
                    detected_category = SupportKnowledgeCategory.PRICE_QUERY
                    matched_kw = kw
                    break

        # Priority 5: SHIPPING QUERY — fall-through (cần AI kiểm tra chính sách thực)
        if not detected_category:
            kws_ship = ["ship", "phí", "giao hàng", "vận chuyển", "nhận hàng"]
            for kw in kws_ship:
                if kw in msg_norm:
                    detected_category = SupportKnowledgeCategory.INFO_SHIPPING
                    matched_kw = kw
                    break

        if not detected_category:
            return None

        tid = current_tenant_id.get() or "default"
        logger.info(f"⚡ [SupportAgent] Sync Heuristic TRIGGERED: category='{detected_category}' | kw='{matched_kw}' | tenant='{tid}'")

        try:
            stmt = select(SupportKnowledge).where(
                and_(
                    SupportKnowledge.deleted_at == None,
                    SupportKnowledge.is_active == True,
                    or_(
                        SupportKnowledge.tenant_id == tid,
                        SupportKnowledge.tenant_id == "default",
                        SupportKnowledge.tenant_id == "smartshop"
                    ),
                    SupportKnowledge.category == detected_category
                )
            ).order_by(SupportKnowledge.priority.desc()).limit(1)

            res = await db.execute(stmt)
            item = res.scalar_one_or_none()

            if item or (detected_category == SupportKnowledgeCategory.PRICE_QUERY and p_info):
                logger.info(f"✅ [SupportAgent] Sync Heuristic HIT: category='{detected_category}'")

                import os
                debug_prefix = f"[L0.5|{detected_category.value}] " if os.getenv("HELEN_DEBUG", "0") == "1" else ""

                # Logic đặc biệt cho PRICE_QUERY (Sử dụng dữ liệu thực tế)
                if detected_category == SupportKnowledgeCategory.PRICE_QUERY and p_info:
                    final_reply = f"{debug_prefix}Dạ liệu trình **{p_info.name}** hiện tại có giá ưu đãi chỉ từ **{p_info.price_display}** ạ. 🌸 Anh/Chị muốn chốt số lượng bao nhiêu để Helen lên đơn ngay cho mình nhé?"
                else:
                    final_reply = f"{debug_prefix}{item.answer}"

                await self._save_history(
                    db, session_id, request.message, final_reply,
                    SupportIntent.POLICY_QUERY if detected_category != SupportKnowledgeCategory.PRICE_QUERY else SupportIntent.PRICE_QUERY,
                    request.product_slug
                )
                await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
                return SupportResponse(
                    ok=True,
                    reply=final_reply,
                    intent=SupportIntent.POLICY_QUERY if detected_category != SupportKnowledgeCategory.PRICE_QUERY else SupportIntent.PRICE_QUERY,
                    session_id=session_id,
                    status="DONE"
                )
            else:
                logger.warning(f"❌ [SupportAgent] Sync Heuristic MISS: No row for category='{detected_category}' | tenant='{tid}'")
                return None
        except Exception as e:
            logger.error(f"[SupportAgent] Sync Heuristic Error: {e}")
            return None

support_agent = SupportAgentOperative()
