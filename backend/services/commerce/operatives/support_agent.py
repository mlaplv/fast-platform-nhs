"""
Support Agent Operative — SUPPORT_NAME_CLIENT
===============================================
PydanticAI-based conversational support agent for the client-facing storefront.
Handles product queries, policy lookups, and general commerce advice.

Architecture:
- Uses TrinityBridge for model routing (role="fast" → flash models)
- Read-only DB access via `read_session.py` provider
- Emits SUPPORT_QUERY_LOG to EventBus (batch, post-session, no PII)
- Logs performance to AgentTelemetryLog
- Strictly isolated from XoHi domain
"""
from __future__ import annotations

import asyncio
import json
import os
import logging
import re
import time
import uuid
from typing import Optional, cast, Union, Any, TYPE_CHECKING, Dict, Type, List

# Type Aliases for 100% Static Typing (CẤM 'any')
JSONValue = Union[str, int, float, bool, None, dict[str, "JSONValue"], list["JSONValue"]]
SupportAIDict = dict[str, Union[str, int, float, bool, None]]

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.commerce import ProductBase
from backend.database.models.content import Category
from backend.database.models.system import AgentTelemetryLog, SupportChatHistory
from backend.schemas.support import SupportIntent, SupportRequest, SupportResponse, SupportProductInfo
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.services.commerce.constants.support_config import support_cfg
from backend.services.commerce.security.input_guard import input_guard
from backend.services.event_bus import event_bus
from backend.services.xohi_memory import xohi_memory
from backend.services.core.zalo_service import zalo_service
from backend.services.commerce.support_knowledge import SupportKnowledgeService
from backend.database.repositories import SupportKnowledgeRepository
from backend.utils.security import GeminiSecurity

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# AGENTIC STRUCTURED RESPONSE (Viral 2026 - Elite V2.2)
# ══════════════════════════════════════════════════════════════
class AgenticSupportResponse(BaseModel):
    model_config = ConfigDict(strict=False)
    reply: str = Field(..., description="Văn bản phản hồi tự nhiên, mượt mà và thuyết phục theo chỉ thị bán hàng. NẾU KHÁCH CHO BIẾT MUỐN MUA SỐ LƯỢNG LỌ CỤ THỂ, BẠN PHẢI TÍNH LUÔN SỐ COMBO VÀ BÁO TỔNG GIÁ + HOA HỒNG.")
    intent: str = Field(..., description="MỘT trong các chuỗi sau: 'ORDER_STATUS', 'ESCALATE', 'POLICY_QUERY', 'PRICE_QUERY', 'PURCHASE', 'GENERAL_ADVICE', 'UNKNOWN'")

class SupportAgentDeps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    db: AsyncSession

from pydantic_ai import Agent, RunContext

# ══════════════════════════════════════════════════════════════
# PYDANTIC AI AGENT — Singleton, initialized once at module load
# ══════════════════════════════════════════════════════════════
_support_ai_agent: Agent[SupportAgentDeps, AgenticSupportResponse] = Agent(
    output_type=AgenticSupportResponse,
    retries=1, # ELITE V2.2: Limited retries to handle transient formatting errors (JSON)
)

@_support_ai_agent.tool

async def get_knowledge_index(ctx: RunContext[SupportAgentDeps]) -> str:
    """
    LAYER 1: Tra cứu mục lục kiến thức Helen đang có. 
    Dùng công cụ này để biết Helen có thông tin gì trước khi tra cứu chi tiết.
    """
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    from backend.database.repositories import SupportKnowledgeRepository
    
    deps = ctx.deps
    repo = SupportKnowledgeRepository(session=deps.db)
    service = SupportKnowledgeService(repo=repo)
    return await service.get_knowledge_index(deps.db)

@_support_ai_agent.tool
async def fetch_topic_details(ctx: RunContext[SupportAgentDeps], topic_id: str) -> str:
    """
    LAYER 2: Tra cứu thông tin chi tiết của một chủ đề dựa trên topic_id từ mục lục.
    """
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    from backend.database.repositories import SupportKnowledgeRepository
    
    deps = ctx.deps
    repo = SupportKnowledgeRepository(session=deps.db)
    service = SupportKnowledgeService(repo=repo)
    return await service.get_topic_details(deps.db, topic_id)

@_support_ai_agent.tool
async def search_knowledge_base(ctx: RunContext[SupportAgentDeps], query: str) -> str:
    """
    LAYER 3: Tìm kiếm mờ (Fuzzy Search) trong toàn bộ kho tri thức. 
    Dùng khi không tìm thấy ID phù hợp trong mục lục hoặc muốn tìm kiếm theo từ khóa tự do.
    """
    from backend.services.commerce.support_knowledge import SupportKnowledgeService
    from backend.database.repositories import SupportKnowledgeRepository
    
    deps = ctx.deps
    repo = SupportKnowledgeRepository(session=deps.db)
    service = SupportKnowledgeService(repo=repo)
    return await service.search_relevant_knowledge(deps.db, query)


# ══════════════════════════════════════════════════════════════
# PRODUCT CONTEXT FETCHER — Read-only, Scalar Projection only
# ══════════════════════════════════════════════════════════════

async def _fetch_product_context(db: AsyncSession, slug: Optional[str]) -> tuple[str, Optional[SupportProductInfo]]:
    """
    Fetch product info for RAG context injection and UI metadata.
    SELECT only — no INSERT/UPDATE/DELETE permitted.
    """
    if not slug:
        return "", None
    try:
        stmt = (
            select(
                ProductBase.id,
                ProductBase.name,
                ProductBase.short_description,
                ProductBase.description,
                ProductBase.price,
                ProductBase.discount_price,
                ProductBase.product_metadata,
                ProductBase.status,
                Category.name.label("category_name"),
            )
            .outerjoin(Category, ProductBase.category_id == Category.id)
            .where(
                and_(
                    ProductBase.slug == slug,
                    ProductBase.deleted_at.is_(None),
                    ProductBase.status == "ACTIVE",
                )
            )
        )
        res = await db.execute(stmt)
        row = res.one_or_none()
        if not row:
            return "", None

        p_info = SupportProductInfo(
            id=str(row.id),
            name=row.name,
            price=float(row.price or 0),
            discount_price=float(row.discount_price or 0) if row.discount_price else None,
            category=row.category_name,
        )

        ctx = (
            f"[SẢN PHẨM HIỆN TẠI]\n"
            f"Tên: {row.name}\n"
            f"Mô tả ngắn: {row.short_description}\n"
            f"Chi tiết: {row.description}\n"
            f"Giá niêm yết: {row.price} VND\n"
        )
        if row.discount_price:
            ctx += f"Giá khuyến mãi: {row.discount_price} VND\n"
        
        return ctx, p_info
    except Exception as e:
        logger.warning("[SupportAgent] Product context fetch failed: %s", e)
        return "", None

def _sanitize_response(text: str) -> str:
    """
    Final security layer: scrub any remaining markdown debris or sensitive system leaks.
    """
    # Remove thought-process leftovers if model leaked them
    clean = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL)
    # Ensure no local file paths or server IPs leaked
    clean = re.sub(r"/\w+/\w+/\w+", "[REDACTED]", clean)
    return clean.strip()

# ══════════════════════════════════════════════════════════════
# SUPPORT AGENT OPERATIVE (Elite V2.2 Refactored for Async)
# ══════════════════════════════════════════════════════════════

class SupportAgentOperative(BaseAgentOperative):
    """
    Client-facing chat operative. Handles intent routing, product RAG,
    and safe AI response generation for SUPPORT_NAME_CLIENT.
    """
    agent_id_class = "support_agent"

    def __init__(self, agent_id: str = "support_agent", **kwargs: object):
        super().__init__(agent_id=agent_id)

    def _handle_layer_1(self, message: str, session_id: str) -> Optional[SupportResponse]:
        """Hybrid Tier 1 (The Butler): Intercepts quick greetings to block wasteful AI calls."""
        _GREETING_PATTERNS: tuple[str, ...] = (
            "chào", "hi", "alo", "shop ơi", "có ai không", ".", "hello", "dạ", "chào bạn", "hello shop", "ê"
        )
        text: str = message.lower().strip()
        
        is_greeting: bool = len(text) < 2 or text in _GREETING_PATTERNS
        if is_greeting:
            return SupportResponse(
                ok=True,
                reply="Dạ Helen đây ạ! Chúc bạn một ngày tốt lành 🌸\nBạn đang cần em hỗ trợ *kiểm tra thông tin Đơn Hàng* hay muốn nhận *Tư Vấn Ưu Đãi* sản phẩm ạ?",
                intent=SupportIntent.GENERAL_ADVICE,
                session_id=session_id,
                status="DONE"
            )
        return None

    def _extract_heuristic_metadata(self, message: str) -> dict[str, Optional[Union[str, bool]]]:
        """
        Elite V2.2: Real-time Heuristic Scanner.
        Extracts VN phone numbers and detects purchase intent via keywords.
        """
        # 1. Phone Scanning (Vietnamese Formats)
        phone_pattern = r"(?:0|\+84)(?:[1-9])(?:\d{8,9}|(?:\.\d{3}){2}\.\d{2,3}|(?:\s\d{3}){2,3})"
        match = re.search(phone_pattern, message)
        phone: Optional[str] = None
        if match:
            phone = match.group(0).replace(".", "").replace(" ", "").replace("-", "")
            if phone.startswith("+84"):
                phone = "0" + phone[3:]

        # 2. Keyword/Intent Overlays (The "Kèo thơm" Scanner)
        high_intent_kws = (
            "ship", "mua", "đặt", "chốt", "địa chỉ", "lọ", "chai", "hộp", "combo", 
            "gửi", "thanh toán", "cho tôi", "cho em", "giao cho", "lấy", "tới địa chỉ", "đặt hàng"
        )
        msg_lower = message.lower()
        is_high_intent = phone is not None or any(kw in msg_lower for kw in high_intent_kws)

        return {
            "extracted_phone": phone,
            "is_high_intent": is_high_intent
        }

        return None

    def get_schema(self) -> Optional[Type[BaseModel]]:
        from backend.schemas.support import SupportRequest
        return SupportRequest

    async def chat(
        self,
        request: SupportRequest,
        db: AsyncSession,
        **kwargs: Any
    ) -> SupportResponse:
        """
        Elite V2.2: Dual-Tier Entry Point (Sync/Async).
        1. Sync Tier (The Butler): Returns 200 OK for Greetings/FAQs.
        2. Async Tier (The Brain): Enqueues Job for LLM/RAG, returns 202 Accepted.
        """
        session_id = request.session_id or str(uuid.uuid4())
        
        # 🚀 TIER 1: THE BUTLER (Synchronous - 0ms AI Coasting)
        # Intercept greetings, spam, or cached FAQs to block wasteful AI calls.
        tier1_reply: Optional[SupportResponse] = self._handle_layer_1(request.message, session_id)
        if tier1_reply:
            await self._save_history(
                db,
                session_id=session_id,
                user_msg=request.message,
                assistant_reply=tier1_reply.reply,
                intent=tier1_reply.intent,
                product_slug=request.product_slug,
                customer_name=request.customer_name,
                customer_phone=request.customer_phone
            )
            return tier1_reply

        # 🛡️ HUMAN TAKEOVER GUARD
        is_takeover = await xohi_memory.client.get(f"support:takeover:{session_id}")
        if is_takeover == "1":
            takeover_msg = "Tư vấn viên đang trực tiếp hỗ trợ sếp. Vui lòng đợi trong giây lát ạ! 🌸"
            return SupportResponse(ok=True, reply=takeover_msg, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")

        # 🚀 TIER 2: THE BRAIN (Asynchronous - arq Worker)
        # Delegate to background worker via the inherited 'enqueue_chat' backdoor.
        task_id = await self.enqueue_chat(
            request_data=request.model_dump(),
            session_id=session_id
        )

        return SupportResponse(
            ok=True,
            reply="Dạ Helen đang xử lý yêu cầu của bạn, chờ em giây lát nhé! 🌸",
            intent=SupportIntent.UNKNOWN,
            session_id=session_id,
            task_id=task_id,
            status="PROCESSING"
        )

    async def process_brain_logic(self, request: SupportRequest, db: AsyncSession) -> SupportResponse:
        """
        Original heavy logic (LLM + RAG + Sanitization).
        Called by the arq Worker's run_agent_task() function.
        """
        t0 = time.monotonic()
        session_id = request.session_id or str(uuid.uuid4())
        
        # Elite V2.2: Lead Extraction & Auto-Draft Conversion
        from backend.services.commerce.logic.lead_extractor import lead_extractor
        lead_data = await lead_extractor.extract_and_convert(
            db, 
            request.message, 
            session_id, 
            current_product_slug=request.product_slug
        )
        if lead_data and lead_data.customer_phone:
            request.customer_phone = lead_data.customer_phone
            request.customer_name = lead_data.customer_name or request.customer_name


        # Chat Context (History)
        history_text = await self._fetch_chat_context(db, session_id)

        # Product Context
        product_ctx, product_info = await _fetch_product_context(db, request.product_slug)

        # Medical Masking
        safe_message: str = await self._mask_sensitive_medical_terms(request.message)

        # Prompt Construction (Elite V2.2: Dynamic Memory Architecture)
        full_directive = await self._build_prompt_directive(product_ctx, history_text)

        # AI Execution via TrinityBridge
        intent = SupportIntent.UNKNOWN
        raw_reply = ""
        try:
            # Prepare deps for Tools (R110)
            deps = SupportAgentDeps(db=db)
            
            result = await trinity_bridge.run(
                _support_ai_agent,
                safe_message, 
                role=support_cfg.model_role,
                system_prompt=full_directive, 
                deps=deps,
                safety_none=True, 
                timeout=15.0
            )
            ai_data = getattr(result, "data", None)
            ai_dict: SupportAIDict = {}
            if ai_data and hasattr(ai_data, "model_dump"):
                ai_dict = cast(SupportAIDict, ai_data.model_dump())
            elif ai_data and hasattr(ai_data, "dict"):
                ai_dict = cast(SupportAIDict, ai_data.dict())
            elif isinstance(ai_data, dict):
                ai_dict = cast(SupportAIDict, ai_data)
            
            raw_reply = str(ai_dict.get("reply", "") or "")
            raw_i = str(ai_dict.get("intent", "UNKNOWN")).upper()
            intent = SupportIntent(raw_i) if raw_i in [i.value for i in SupportIntent] else SupportIntent.UNKNOWN
        except Exception as exc:
            logger.error("[SupportAgent] AI call failed: %s", exc)
            raw_reply = "Xin lỗi, hệ thống đang bận. Mời quý khách liên hệ hotline để được hỗ trợ ngay ạ!"

        safe_reply = _sanitize_response(raw_reply)
        duration_ms = int((time.monotonic() - t0) * 1000)

        # Persist and Notify
        await self._save_history(
            db,
            session_id=session_id,
            user_msg=request.message,
            assistant_reply=safe_reply,
            intent=intent,
            product_slug=request.product_slug,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone
        )
        
        # Emit Telemetry & Pulse
        await event_bus.emit("SUPPORT_QUERY_LOG", {"session_id": session_id, "intent": intent.value, "duration_ms": duration_ms})
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
        
        # R82.31: Client-side Pulse Delivery
        await event_bus.emit("SUPPORT_RESPONSE_READY", {
            "session_id": session_id,
            "reply": safe_reply,
            "intent": intent.value,
            "status": "DONE"
        })


        return SupportResponse(
            ok=True,
            reply=safe_reply,
            intent=intent,
            session_id=session_id,
            product_info=product_info,
            status="DONE"
        )

    async def _save_history(self, db: AsyncSession, session_id: str, user_msg: str, assistant_reply: str, intent: SupportIntent, product_slug: Optional[str], customer_name: Optional[str] = None, customer_phone: Optional[str] = None) -> None:
        try:
            enc_user_msg = GeminiSecurity.encrypt(user_msg)
            enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)
            user_hist = SupportChatHistory(session_id=session_id, role="user", content=enc_user_msg, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            assistant_hist = SupportChatHistory(session_id=session_id, role="assistant", content=enc_assistant_reply, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            db.add_all([user_hist, assistant_hist])
            await db.commit()
        except Exception as exc:
            logger.warning("[SupportAgent] Failed to save chat history: %s", exc)
            await db.rollback()

    async def _fetch_chat_context(self, db: AsyncSession, session_id: str) -> str:
        history_text = ""
        try:
            stmt = select(SupportChatHistory).where(SupportChatHistory.session_id == session_id).order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id)).limit(4)
            history_res = await db.execute(stmt)
            history_rows = history_res.scalars().all()
            if history_rows:
                h_parts = []
                for r in reversed(history_rows):
                    h_content = GeminiSecurity.decrypt(r.content) if r.content else ""
                    h_role = "Khách" if r.role == "user" else "Helen"
                    h_parts.append(f"{h_role}: {h_content}")
                history_text = "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n"
        except Exception as h_exc:
            logger.warning("[SupportAgent] Context retrieval failed: %s", h_exc)
        return history_text

    async def _build_prompt_directive(self, product_ctx: str, history_text: str = "") -> str:
        ctx_block: str = f"\n{product_ctx}\n" if (product_ctx) else ""
        agentic_directive = await xohi_memory.client.get("support:agent:system_prompt")
        if not agentic_directive:
            try:
                if os.path.exists(support_cfg.prompt_template_path):
                    with open(support_cfg.prompt_template_path, "r", encoding="utf-8") as f:
                        agentic_directive = f.read()
                else:
                    agentic_directive = support_cfg.system_directive
            except Exception:
                agentic_directive = support_cfg.system_directive
        return (
            f"{agentic_directive}\n{history_text}\n"
            "[KNOWLEDGE CONTEXT]\n"
            f"{ctx_block}\n"
            "MẸO: Bạn hỗ trợ Kiến trúc bộ nhớ 3 lớp. Hãy dùng tool 'get_knowledge_index' để xem các chủ đề Helen đang biết, "
            "sau đó dùng 'fetch_topic_details' để lấy kiến thức chi tiết nếu cần tư vấn sâu hơn.\n"
            "--- BẮT ĐẦU PHÂN TÍCH VÀ PHẢN HỒI ---"
        )

# Module-level singleton
support_agent = SupportAgentOperative()
