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
            image_url=img_url,
            stock=p.stock
        )
        ctx = f"[SẢN PHẨM HIỆN TẠI]\nTên: {p.name}\nMô tả: {p.short_description}\nGiá niêm yết: {p.price} VND\n"
        if p.discount_price: ctx += f"Giá khuyến mãi: {p.discount_price} VND\n"
        ctx += f"Tồn kho thực tế: {p.stock or 0} lọ\n"
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
        self.router = SupportRouter()

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
                h_content = GeminiSecurity.decrypt(r.content or "")
                h_role = "Khách" if r.role == "user" else "Helen"
                h_parts.append(f"{h_role}: {h_content}")
            return "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n"
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

    async def chat(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        """
        Elite V2.5: Entry Protocol.
        L0: Fast-Path LLM (<200ms) - Intent Classification
        L1: Deep Brain (Background Task) - Orchestrated Specialists
        """
        session_id = request.session_id or str(uuid.uuid4())
        
        # 🚀 FAST-PATH (Intent Classification Only)
        # We skip Fast-Path for Strategic Specialist Products to ensure deep reasoning
        if request.product_slug == support_cfg.hong_son_slug:
            logger.info("[SupportAgent] Lockdown: Bypassing Fast-Path for Deep Specialist.")
        else:
            try:
                fast_res = await trinity_bridge.run(_fast_intent_agent, request.message, role=trinity_bridge.ROLE_FAST, timeout=2.0)
                f_data = cast(FastIntentResponse, fast_res.data) # Proper Elite V2.2 Typing
                
                if f_data.intent == "GREETING" and f_data.quick_reply:
                    await self._save_history(db, session_id, request.message, f_data.quick_reply, SupportIntent.GENERAL_ADVICE, request.product_slug)
                    return SupportResponse(ok=True, reply=f_data.quick_reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")
            except Exception as e:
                logger.warning("[SupportAgent] Fast-Path Bypass: %s", e)

        # 🚀 DEEP BRAIN (Background Task)
        task_id = await self.enqueue_chat(request_data=request.model_dump(), session_id=session_id)
        return SupportResponse(ok=True, reply="Helen đang xử lý...", intent=SupportIntent.UNKNOWN, session_id=session_id, task_id=task_id, status="PROCESSING")

support_agent = SupportAgentOperative()
