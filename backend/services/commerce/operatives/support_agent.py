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

# Type Aliases for 100% Static Typing (Elite Protocol)
JSONValue = Union[str, int, float, bool, None, dict[str, "JSONValue"], list["JSONValue"]]
SupportAIDict = dict[str, Union[str, int, float, bool, None]]

from pydantic import BaseModel, ConfigDict, Field
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
    reply: str = Field(..., description="Văn bản phản hồi tự nhiên, mượt mà và thuyết phục theo chỉ thị Martial Combo Protocol.")
    intent: str = Field(..., description="MỘT trong các chuỗi sau: 'ORDER_STATUS', 'ESCALATE', 'POLICY_QUERY', 'PRICE_QUERY', 'PURCHASE', 'GENERAL_ADVICE', 'UNKNOWN'")

class SupportAgentDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession

# ══════════════════════════════════════════════════════════════
# PYDANTIC AI AGENT — Singleton (Architect Optimized)
# ══════════════════════════════════════════════════════════════
_support_ai_agent: Agent[SupportAgentDeps, AgenticSupportResponse] = Agent(
    output_type=AgenticSupportResponse,
    retries=1, 
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
        p_info = SupportProductInfo(id=str(p.id), name=p.name, price=float(p.price or 0), price_display=f"{int(p.discount_price or p.price or 0):,}đ".replace(",", "."), slug=slug or "")
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

    def __init__(self, agent_id: str = "support_agent", **kwargs: object):
        super().__init__(agent_id=agent_id)

    async def _save_history(self, db: AsyncSession, session_id: str, user_msg: str, assistant_reply: str, intent: SupportIntent, product_slug: Optional[str], customer_name: Optional[str] = None, customer_phone: Optional[str] = None) -> None:
        """Encrypted transactional history persistence."""
        try:
            enc_user_msg = GeminiSecurity.encrypt(user_msg)
            enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)
            msg_user = SupportChatHistory(session_id=session_id, role="user", content=enc_user_msg, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            msg_ai = SupportChatHistory(session_id=session_id, role="assistant", content=enc_assistant_reply, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            db.add_all([msg_user, msg_ai])
            await db.flush()
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

    def _calculate_delivery_time(self, address: str) -> str:
        """Elite V2.5 High-Fidelity Shipping Estimator."""
        if not address: return "2-3 ngày"
        addr: str = address.lower()
        hcm_keys: List[str] = ["hồ chí minh", "tp.hcm", "hcm", "sài gòn", "phú lâm", "quận 1", "quận 2", "quận 3", "quận 4", "quận 5", "quận 6", "quận 7", "quận 8", "quận 9", "quận 10", "quận 11", "quận 12", "bình tân", "bình thạnh", "gò vấp", "phú nhuận", "tân bình", "tân phú", "thủ đức", "hóc môn", "củ chi", "nhà bè", "bình chánh", "cần giờ"]
        if any(key in addr for key in hcm_keys): return "1-2 ngày"
        south_keys: List[str] = ["bình phước", "bình dương", "đồng nai", "tây ninh", "vũng tàu", "long an", "tiền giang", "vĩnh long", "bến tre", "kiên giang", "cần thơ", "hậu giang", "trà vinh", "sóc trăng", "bạc liêu", "cà mau"]
        if any(key in addr for key in south_keys): return "2-3 ngày"
        return "3-5 ngày"

    async def _build_prompt_directive(self, product_ctx: str, history_text: str = "", lead_metadata: Optional[Dict[str, object]] = None) -> str:
        """Strategic Sales Prompt Construction."""
        agentic_directive = await xohi_memory.client.get("support:agent:system_prompt")
        if not agentic_directive:
            try:
                if os.path.exists(support_cfg.prompt_template_path):
                    async with asyncio.to_thread(open, support_cfg.prompt_template_path, "r", encoding="utf-8") as f:
                        agentic_directive = f.read()
                else: agentic_directive = support_cfg.system_directive
            except: agentic_directive = support_cfg.system_directive

        # 🚀 MARTIAL COMBO PROTOCOL (R0.3 Evolution)
        rules = (
            "\n[SALES PROTOCOL: MARTIAL COMBO]\n"
            "1. 1 Lọ: 249k.\n"
            "2. 2-3 Lọ -> Combo 3: 498k (Mua 2 tặng 1).\n"
            "3. 4-6 Lọ -> Combo 6: 996k (Mua 4 tặng 2).\n"
            "4. >6 Lọ: Block chốt đơn, báo đợi chuyên viên báo giá sỉ.\n"
            "Khuyến khích khách mua Combo để tiết kiệm nhất.\n"
        )
        
        meta_str = ""
        if lead_metadata:
            meta_str = "\n[SYSTEM ALERT]\n"
            if lead_metadata.get("is_new_customer"): meta_str += "- Khách hàng MỚI.\n"
            if lead_metadata.get("needs_price_quote"): meta_str += "- CẢNH BÁO: Số lượng sỉ (>6), KHÔNG báo giá tự động.\n"

        return f"{agentic_directive}\n{rules}\n{meta_str}\n{history_text}\n--- PRODUCT ---\n{product_ctx}\n"

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
                delivery_info: str = self._calculate_delivery_time(order_obj.customer_address or "")
                
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
        prompt = await self._build_prompt_directive(ctx_text, hist_text, lead_metadata=lead_meta)
        
        try:
            res = await trinity_bridge.run(_support_ai_agent, request.message, role=support_cfg.model_role, system_prompt=prompt, deps=SupportAgentDeps(db=db), timeout=15.0)
            data: AgenticSupportResponse = res.data # type: ignore
            raw_reply = data.reply or "Dạ Helen đã ghi nhận thông tin ạ!"
            raw_intent = data.intent or "UNKNOWN"
        except Exception as e:
            logger.error("[SupportAgent] Sweep Failure: %s", e)
            raw_reply = "Dạ hệ thống Helen đang bảo trì nhẹ một xíu, Sếp đợi em nhé! 🌸"
            raw_intent = "UNKNOWN"

        safe_reply = _sanitize_response(raw_reply)
        await self._save_history(db, session_id, request.message, safe_reply, SupportIntent(raw_intent) if raw_intent in [i.value for i in SupportIntent] else SupportIntent.UNKNOWN, request.product_slug, request.customer_name, request.customer_phone)
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
        return SupportResponse(ok=True, reply=safe_reply, intent=SupportIntent(raw_intent), session_id=session_id, product_info=p_info, status="DONE")

    async def chat(self, request: SupportRequest, db: AsyncSession, **kwargs: object) -> SupportResponse:
        """Tiered Entry Protocol."""
        session_id = request.session_id or str(uuid.uuid4())
        msg_norm = request.message.lower().strip()
        if msg_norm in ["hi", "hello", "chào", "alo", "helen"]:
            reply = "Dạ Helen đây ạ! Sếp cần em hỗ trợ gì cho đơn hàng của mình không ạ? 🌸"
            await self._save_history(db, session_id, request.message, reply, SupportIntent.GENERAL_ADVICE, request.product_slug)
            return SupportResponse(ok=True, reply=reply, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")
        
        task_id = await self.enqueue_chat(request_data=request.model_dump(), session_id=session_id)
        return SupportResponse(ok=True, reply="Helen đang xử lý...", intent=SupportIntent.UNKNOWN, session_id=session_id, task_id=task_id, status="PROCESSING")

support_agent = SupportAgentOperative()
