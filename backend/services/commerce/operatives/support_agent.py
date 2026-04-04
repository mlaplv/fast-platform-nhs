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
from typing import Optional, cast, Union, TYPE_CHECKING, Dict, Type, List

# Type Aliases for 100% Static Typing (CẤM 'any')
JSONValue = Union[str, int, float, bool, None, dict[str, "JSONValue"], list["JSONValue"]]
SupportAIDict = dict[str, Union[str, int, float, bool, None]]

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.commerce import ProductBase, Order
from backend.database.models.content import Category
from backend.database.models.system import AgentTelemetryLog, SupportChatHistory
from backend.schemas.support import SupportIntent, SupportRequest, SupportResponse, SupportProductInfo
from backend.services.ai_engine.core.vector_memory import VectorMemory
from backend.services.ai_engine.core.semantic_cache import semantic_cache
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
    return await service.fetch_topic_details(deps.db, topic_id)

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
            price_display=f"{int(row.discount_price or row.price or 0):,}đ".replace(",", "."),
            slug=slug or "",
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
                reply="Dạ Helen đây ạ! Chúc quý khách một ngày tốt lành 🌸\nQuý khách đang cần em hỗ trợ *kiểm tra thông tin Đơn Hàng* hay muốn nhận *Tư Vấn Ưu Đãi* sản phẩm ạ?",
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

    def get_schema(self) -> Optional[Type[BaseModel]]:
        from backend.schemas.support import SupportRequest
        return SupportRequest

    async def chat(
        self,
        request: SupportRequest,
        db: AsyncSession,
        **kwargs: object
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
            takeover_msg = "Chuyên viên tư vấn đang trực tiếp hỗ trợ quý khách. Vui lòng đợi trong giây lát ạ! 🌸"
            return SupportResponse(ok=True, reply=takeover_msg, intent=SupportIntent.GENERAL_ADVICE, session_id=session_id, status="DONE")

        # 🛡️ SEMANTIC CACHE LAYER (Elite V2.2)
        cached_reply = await semantic_cache.get(request.message)
        if cached_reply:
            await self._save_history(
                db,
                session_id=session_id,
                user_msg=request.message,
                assistant_reply=cached_reply,
                intent=SupportIntent.GENERAL_ADVICE,
                product_slug=request.product_slug,
                customer_name=request.customer_name,
                customer_phone=request.customer_phone
            )
            return SupportResponse(
                ok=True,
                reply=cached_reply,
                intent=SupportIntent.GENERAL_ADVICE,
                session_id=session_id,
                status="DONE"
            )

        # 🚀 TIER 2: THE BRAIN (Asynchronous - arq Worker)
        # Delegate to background worker via the inherited 'enqueue_chat' backdoor.
        task_id = await self.enqueue_chat(
            request_data=request.model_dump(),
            session_id=session_id
        )

        return SupportResponse(
            ok=True,
            reply="Dạ Helen đang xử lý yêu cầu của quý khách, chờ em giây lát nhé! 🌸",
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
        if lead_data:
            request.customer_phone = lead_data.customer_phone or request.customer_phone
            request.customer_name = lead_data.customer_name or request.customer_name
            
            order_id_val: object = getattr(lead_data, "processed_order_id", None)
            order_id: Union[str, None] = str(order_id_val) if order_id_val else None

            if order_id is not None:
                # DETERMINISTIC SHORT-CIRCUIT: Bypass LLM entirely if order created
                # Elite V2.5: Refined Confirmation with Dynamic Shipping & Caching (V-CTO)
                
                # Fetch full order for accurate details (totals, items, address)
                # No 'any' rule (R2.2)
                from sqlalchemy import select
                order_stmt = select(Order).where(Order.id == order_id)
                order_res = await db.execute(order_stmt)
                order_obj: Union[Order, None] = order_res.scalar_one_or_none()
                
                if order_obj:
                    # 1. Shorten Order ID (Shopee Style)
                    short_id: str = order_id[-8:].upper()
                    
                    # 2. Calculate Item Count
                    total_qty: int = 0
                    if isinstance(order_obj.items, list):
                        for it in order_obj.items:
                            if isinstance(it, dict):
                                total_qty += int(it.get("quantity", 1))
                    
                    # 3. Format Amount (VN Standard)
                    formatted_total: str = "{:,.0f}".format(float(order_obj.total_amount or 0)).replace(",", ".")
                    
                    # 4. Dynamic Shipping Estimate (Helen Brain Protocol)
                    delivery_days: str = self._calculate_delivery_time(order_obj.customer_address or "")
                    
                    # 5. Build Final Reply with Action Button (Elite V2.2 Markdown)
                    safe_reply: str = (
                        "Dạ Helen xin cảm ơn quý khách! 🌸\n"
                        "Đơn hàng của quý khách đã được lên thành công:\n"
                        f"- Mã đơn: **{short_id}**\n"
                        f"- Số sản phẩm: {total_qty} lọ/combo\n"
                        f"- Tổng tiền: **{formatted_total}đ** (đã free ship)\n"
                        f"- Dự kiến nhận hàng: **{delivery_days}**\n\n"
                        "Mời quý khách nhấn vào bên dưới để theo dõi:\n"
                        f"[🔍 KIỂM TRA ĐƠN HÀNG](https://smartshop.test/account/orders/{order_id})\n\n"
                        "Tổng đài viên sẽ sớm gọi điện xác nhận lại cho quý khách nhé ạ!"
                    )
                else:
                    # Fallback if DB fetch fails
                    safe_reply = f"Dạ Helen xin cảm ơn quý khách! Đơn hàng của quý khách (Mã đơn: {order_id[-8:].upper()}) đã được lên thành công. Tổng đài viên sẽ sớm gọi điện xác nhận lại nhé ạ! 🌸"

                from backend.schemas.support import SupportIntent
                intent: SupportIntent = SupportIntent.PURCHASE
                duration_ms: int = int((time.monotonic() - t0) * 1000)
                
                # Fetch product info for the response metadata
                _, product_info = await _fetch_product_context(db, request.product_slug)
                
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
                
                await event_bus.emit("SUPPORT_QUERY_LOG", {"session_id": session_id, "intent": intent.value, "duration_ms": duration_ms})
                await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
                
                # Redis Broadcast to Admin (Elite V2.2 Cross-Container Sync)
                try:
                    if xohi_memory._use_redis and getattr(xohi_memory, "client", None):
                        redis_payload: str = json.dumps({"event": "SUPPORT_INBOX_UPDATE", "payload": {"session_id": session_id}}, ensure_ascii=False)
                        await xohi_memory.client.publish("admin:pulse", redis_payload)
                except Exception as rb_exc:
                    logger.warning("[SupportAgent] Redis broadcast to admin:pulse failed: %s", rb_exc)

                return SupportResponse(
                    ok=True,
                    reply=safe_reply,
                    intent=intent,
                    session_id=session_id,
                    product_info=product_info, # type: ignore
                    status="DONE"
                )

            lead_metadata: Union[Dict[str, object], None] = {
                "is_new_customer": lead_data.is_new_customer,
                "address_status": getattr(lead_data, "address_status", "UNKNOWN"),
                "previous_address": getattr(lead_data, "previous_address", None)
            }
        else:
            lead_metadata = None


        # Chat Context (History)
        history_text = await self._fetch_chat_context(db, session_id)

        # Product Context
        product_ctx, product_info = await _fetch_product_context(db, request.product_slug)

        # Medical Masking
        safe_message: str = await self._mask_sensitive_medical_terms(request.message)

        # Prompt Construction (Elite V2.2: Dynamic Memory Architecture)
        full_directive = await self._build_prompt_directive(product_ctx, history_text, lead_metadata=lead_metadata)

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

        if not raw_reply.strip():
            logger.warning("[SupportAgent] AI returned empty reply! Applying safety fallback.")
            raw_reply = "Dạ hệ thống đã ghi nhận thông tin của quý khách. Quý khách có cần em hỗ trợ thêm gì không ạ?"

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
        
        # Emit Telemetry & Pulse via Central Neural System (Worker handles binary commit)
        await event_bus.emit("SUPPORT_QUERY_LOG", {"session_id": session_id, "intent": intent.value, "duration_ms": duration_ms})
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
        
        # Redis Broadcast to Admin (Elite V2.2 Cross-Container Sync)
        try:
            if xohi_memory._use_redis and getattr(xohi_memory, "client", None):
                redis_payload = json.dumps({
                    "event": "SUPPORT_INBOX_UPDATE", 
                    "payload": {"session_id": session_id}
                }, ensure_ascii=False)
                await xohi_memory.client.publish("admin:pulse", redis_payload)
        except Exception as rb_exc:
            logger.warning("[SupportAgent] Redis broadcast to admin:pulse failed: %s", rb_exc)

        
        # [ELITE BUGFIX] Removing direct SUPPORT_RESPONSE_READY emission here.
        # The arq Worker (arq_worker.py) now handles this after the final atomic commit
        # to ensure the UI only receives data that is actually persisted in the DB.


        return SupportResponse(
            ok=True,
            reply=safe_reply,
            intent=intent,
            session_id=session_id,
            product_info=product_info,
            status="DONE"
        )

    def _calculate_delivery_time(self, address: str) -> str:
        """
        Elite V2.5: Dynamic Shipping Estimation (Helen Brain Intelligence).
        Refined logic based on regional keywords.
        """
        if not address:
            return "2-3 ngày"
            
        addr: str = address.lower()
        
        # 1. HCM (1-2 days)
        hcm_keys: list[str] = ["hồ chí minh", "tp.hcm", "hcm", "sài gòn", "phú lâm", "quận 1", "quận 2", "quận 3", "quận 4", "quận 5", "quận 6", "quận 7", "quận 8", "quận 9", "quận 10", "quận 11", "quận 12", "bình tân", "bình thạnh", "gò vấp", "phú nhuận", "tân bình", "tân phú", "thủ đức", "hóc môn", "củ chi", "nhà bè", "bình chánh", "cần giờ"]
        if any(key in addr for key in hcm_keys):
            return "1-2 ngày"
            
        # 2. Southern Provinces (2-3 days)
        south_keys: list[str] = [
            "bình phước", "bình dương", "đồng nai", "tây ninh", "vũng tàu", 
            "long an", "đồng tháp", "an giang", "tiền giang", "vĩnh long", 
            "bến tre", "kiên giang", "cần thơ", "hậu giang", "trà vinh", 
            "sóc trăng", "bạc liêu", "cà mau"
        ]
        if any(key in addr for key in south_keys):
            return "2-3 ngày"
            
        # 3. Other regions (3-5 days)
        return "3-5 ngày"

    async def _save_history(self, db: AsyncSession, session_id: str, user_msg: str, assistant_reply: str, intent: SupportIntent, product_slug: Optional[str], customer_name: Optional[str] = None, customer_phone: Optional[str] = None) -> None:
        try:
            enc_user_msg = GeminiSecurity.encrypt(user_msg)
            enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)
            user_hist = SupportChatHistory(session_id=session_id, role="user", content=enc_user_msg, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            assistant_hist = SupportChatHistory(session_id=session_id, role="assistant", content=enc_assistant_reply, intent=intent.value, product_slug=product_slug, customer_name=customer_name, customer_phone=customer_phone)
            db.add_all([user_hist, assistant_hist])
            # [ELITE R0.2] Using flush() instead of commit() to allow Atomic Transaction 
            # management at the Worker/Controller level.
            await db.flush()
        except Exception as exc:
            logger.warning("[SupportAgent] Failed to save chat history: %s", exc)
            # No rollback() here - let the outer owner handle failure.

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

    async def _build_prompt_directive(self, product_ctx: str, history_text: str = "", lead_metadata: Optional[Dict[str, object]] = None) -> str:
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
        
        # Inject Identity-First Metadata for Retention Engine (Elite V2.2)
        if lead_metadata:
            id_ctx = (
                "\n[CUSTOMER IDENTITY CONTEXT]\n"
                f"is_new_customer: {lead_metadata.get('is_new_customer')}\n"
                f"address_status: {lead_metadata.get('address_status')}\n"
                f"previous_address: {lead_metadata.get('previous_address') or 'N/A'}\n"
                "QUY TẮC: Dùng thông tin trên để cá nhân hóa lời chào và xác nhận địa chỉ nếu cần.\n"
            )
            
            agentic_directive = id_ctx + agentic_directive

        return (
            f"{agentic_directive}\n{history_text}\n"
            "[KIẾN TRÚC TRI THỨC 3 LỚP (ELITE V2.2)]\n"
            "Bạn có quyền truy cập hệ thống tri thức phân tầng để trả lời chính xác nhất:\n"
            "1. LỚP 1 (Mục lục): Dùng 'get_knowledge_index' để xem danh sách các chủ đề Helen đang biết.\n"
            "2. LỚP 2 (Chi tiết): Dùng 'fetch_topic_details(topic_id)' để lấy nội dung chi tiết của một chủ đề cụ thể.\n"
            "3. LỚP 3 (Tìm kiếm nâng cao): Dùng 'search_knowledge_base(query)' để tìm kiếm mờ khi lớp 1 & 2 không có câu trả lời trực tiếp.\n"
            "--- THÔNG TIN SẢN PHẨM HIỆN TẠI ---\n"
            f"{ctx_block or 'Không có sản phẩm cụ thể đang xem.'}\n"
            "--- BẮT ĐẦU PHÂN TÍCH VÀ PHẢN HỒI ---"
        )

# Module-level singleton
support_agent = SupportAgentOperative()
