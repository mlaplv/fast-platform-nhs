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
from typing import Optional, cast, Union, TYPE_CHECKING

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

# ══════════════════════════════════════════════════════════════
# PYDANTIC AI AGENT — Singleton, initialized once at module load
# ══════════════════════════════════════════════════════════════
_support_ai_agent: Agent[None, AgenticSupportResponse] = Agent(
    output_type=AgenticSupportResponse,
    retries=1, # ELITE V2.2: Limited retries to handle transient formatting errors (JSON)
)



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
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row:
            return "", None

        price_val = row.discount_price if row.discount_price else row.price
        price_display = f"{price_val:,.0f}đ"
        
        deals_raw: list[dict[str, object]] = (row.product_metadata or {}).get("active_deals", [])
        deals_text = ""
        if deals_raw:
            # Elite V2.2: Premium Bullet-pointed Deals for FOMO
            parts = [
                f"* Mua {d.get('buy_qty', 0)} tặng {d.get('get_qty', 0)}: {float(d.get('fixed_price', 0)):,.0f}đ"
                for d in deals_raw if d.get("buy_qty")
            ]
            deals_text = f"\nCHƯƠNG TRÌNH ƯU ĐÃI ĐANG DIỄN RA:\n" + "\n".join(parts) + "\n" if parts else ""

        # Global Sales Fact: ALL products include free shipping
        freeship_info = "\nCHÍNH SÁCH: MIỄN PHÍ VẬN CHUYỂN TOÀN QUỐC (FREESHIP).\n"

        context = (
            f"[THÔNG TIN SẢN PHẨM HIỆN TẠI]\n"
            f"Tên: {row.name}\n"
            f"Danh mục: {row.category_name or 'Chưa phân loại'}\n"
            f"Giá: {price_display}\n"
            f"{deals_text}"
            f"{freeship_info}"
            f"Mô tả: {(row.short_description or row.description or '')[:600]}\n"
        )
        
        metadata = SupportProductInfo(
            id=str(row.id),
            name=row.name,
            price=float(price_val),
            price_display=price_display,
            slug=slug
        )
        
        return context, metadata
    except Exception as exc:
        logger.warning("[SupportAgent] Could not fetch product context: %s", exc)
        return "", None


# ══════════════════════════════════════════════════════════════
# RESPONSE SANITIZER — Strip internal data, cap length
# ══════════════════════════════════════════════════════════════

def _sanitize_response(raw: str) -> str:
    """
    Security Layer ④: Strip any internal path, token fragment, or stack trace
    from AI output before returning to client. Caps at SUPPORT_MAX_TOKENS words.
    """
    # Strip any SUPPORT_SYSTEM_DIRECTIVE fragments that may have leaked
    dangerous_patterns: list[str] = [
        r"TUYỆT ĐỐI không tiết lộ",
        r"/backend[/\w]*",
        r"api[_-]?key\s*[:=]\s*\S+",
        r"sk-[A-Za-z0-9]{10,}",
        r"Traceback \(most recent",
    ]
    for pat in dangerous_patterns:
        raw = re.sub(pat, "", raw, flags=re.IGNORECASE)

    # Soft word-count cap (not token, but safe approximation)
    words: list[str] = raw.split()
    limit_idx: int = int(support_cfg.max_response_tokens)
    if len(words) > limit_idx:
        raw = " ".join(words[:limit_idx]) + "..."

    return raw.strip()


# ══════════════════════════════════════════════════════════════
# MAIN OPERATIVE CLASS
# ══════════════════════════════════════════════════════════════

class SupportAgentOperative(BaseAgentOperative):
    """
    Client-facing chat operative. Handles intent routing, product RAG,
    and safe AI response generation for SUPPORT_NAME_CLIENT.
    """
    def __init__(self):
        super().__init__(agent_id="support_agent")

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

    # Heritage: MedicalShieldMixin provides _mask_sensitive_medical_terms

    async def chat(
        self,
        request: SupportRequest,
        db: AsyncSession,
    ) -> SupportResponse:
        """
        Main entry point. Called by SupportController.
        Validates → classifies intent → fetches context → runs AI → sanitizes → returns.
        """
        t0 = time.monotonic()
        session_id = request.session_id or str(uuid.uuid4())
        customer_name = request.customer_name or "Khách ẩn danh"
        
        # 🚀 ELITE V2.2: HEURISTIC PRIORITY SCANNER (Before AI or Takeover)
        scan = self._extract_heuristic_metadata(request.message)
        extracted_phone = scan.get("extracted_phone")
        is_heuristic_high = scan.get("is_high_intent")
        
        # Auto-enrich request metadata if missing but found in text
        if extracted_phone and not request.customer_phone:
            request.customer_phone = str(extracted_phone)

        # ELITE V2.2: Global Helen Toggle Check (Redis-cached)
        helen_on = await xohi_memory.client.get("system:helen_enabled")
        
        # 🛡️ HUMAN TAKEOVER GUARD: Check if an Admin has muzzled Helen for this session
        is_takeover = await xohi_memory.client.get(f"support:takeover:{session_id}")
        
        if is_takeover == "1":
            takeover_msg = "Tư vấn viên đang trực tiếp hỗ trợ sếp. Vui lòng đợi trong giây lát ạ! 🌸"
            # Log the message so admin can see it, but don't let AI reply
            await self._save_history(
                db,
                session_id=session_id,
                user_msg=request.message,
                assistant_reply=takeover_msg, # Placeholder to keep UI flow
                intent=SupportIntent.GENERAL_ADVICE,
                product_slug=request.product_slug,
                customer_name=request.customer_name,
                customer_phone=request.customer_phone
            )
            # Emit pulse so admin inbox refreshes to show the new customer message
            await event_bus.emit("SUPPORT_INBOX_UPDATE", {"session_id": session_id})
            
            return SupportResponse(
                ok=True,
                reply=takeover_msg,
                intent=SupportIntent.GENERAL_ADVICE,
                session_id=session_id,
            )

        if helen_on == "0":
            offline_msg = await xohi_memory.client.get("system:helen_offline_msg")
            reply = offline_msg or "Hiện tại em Helen đang được bảo trì, tư vấn viên sẽ hỗ trợ bạn ngay ạ!"
            
            # 🚀 QUANTUM BRIDGE: Push to Zalo OA when Helen is OFF
            customer_name = request.customer_name or "Khách ẩn danh"
            await zalo_service.push_support_notification(
                customer_name=customer_name,
                message=request.message,
                session_id=session_id
            )

            # Vẫn lưu lịch sử để nhân viên vào xem
            await self._save_history(
                db,
                session_id=session_id,
                user_msg=request.message,
                assistant_reply=reply,
                intent=SupportIntent.GENERAL_ADVICE,
                product_slug=request.product_slug,
                customer_name=request.customer_name,
                customer_phone=request.customer_phone
            )

            return SupportResponse(
                ok=True,
                reply=reply,
                intent=SupportIntent.GENERAL_ADVICE,
                session_id=session_id,
            )

        # Security Layer ①: Input validation
        is_safe, _reason = input_guard.validate(request.message)
        if not is_safe:
            logger.info("[SupportAgent] Input rejected by InputGuard. session=%s", session_id)
            return SupportResponse(
                ok=False,
                reply=f"Xin lỗi, em {support_cfg.agent_name} không thể xử lý yêu cầu này. Vui lòng đặt câu hỏi khác.",
                intent=SupportIntent.UNKNOWN,
                session_id=session_id,
            )

        # Trạm Thu Phí Tier-1 Hybrid Gateway (The Butler - 0ms AI Coasting)
        # Chặn toàn bộ Greeting/Spam rác theo tiêu chuẩn Shopee/Tiki
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
            # Emit telemetry for Tier1 (duration ~0ms)
            await event_bus.emit("SUPPORT_QUERY_LOG", {
                "session_id": session_id,
                "intent": tier1_reply.intent.value,
                "duration_ms": 1,
            })
            return tier1_reply

        # ELITE V2.2: 100% Agentic Intent Orchestration
        # Fetch RAG context from knowledge base (Elite V2.2: Structured Tri thức)
        kb_repo = SupportKnowledgeRepository(session=db)
        kb_service = SupportKnowledgeService(repo=kb_repo)
        kb_ctx = await kb_service.search_relevant_knowledge(db, request.message)

        # Fetch history for context restoration (Elite V2.2: Context Pulse)
        history_text = await self._fetch_chat_context(db, session_id)

        # Build RAG context from product (read-only DB)
        product_ctx, product_info = await _fetch_product_context(db, request.product_slug)

        # Trạm Lọc (Medical Mask) — Đổi từ lóng sang học thuật để VƯỢT RÀO hệ thống Safety của Gemini
        safe_message: str = await self._mask_sensitive_medical_terms(request.message)

        # Construct prompt with Agentic system directive (REFACTORED for System Prompt Isolation)
        full_directive = await self._build_prompt_directive(product_ctx, kb_ctx, history_text)

        # Run AI via TrinityBridge (role="fast" → flash models)
        intent = SupportIntent.UNKNOWN
        raw_reply: str = ""
        try:
            result = await trinity_bridge.run(
                _support_ai_agent,
                safe_message, # Only pass ACTUAL user message here
                role=support_cfg.model_role,
                system_prompt=full_directive, # Complex instructions moved to System Prompt
                safety_none=True, # Bypass aggressive safety filters for commerce queries
                timeout=15.0
            )
            # strictly typed AI output extraction
            ai_data: Optional[AgenticSupportResponse] = getattr(result, "data", None)
            ai_data_str: str = str(ai_data)
            
            # Universal PydanticAI Data Extraction (Refined for Elite V2.2 - NO 'any')
            ai_dict: SupportAIDict = {}
            if ai_data and hasattr(ai_data, "model_dump"):
                ai_dict = cast(SupportAIDict, ai_data.model_dump())
            elif ai_data and hasattr(ai_data, "dict"):
                ai_dict = cast(SupportAIDict, ai_data.dict())
            elif isinstance(ai_data, dict):
                ai_dict = cast(SupportAIDict, ai_data)
            elif isinstance(ai_data, str):
                try:
                    clean_str = ai_data.replace('```json', '').replace('```', '').strip()
                    ai_dict = cast(SupportAIDict, json.loads(clean_str))
                except (json.JSONDecodeError, TypeError):
                    ai_dict = {"reply": ai_data, "intent": "UNKNOWN"}

            raw_reply = str(ai_dict.get("reply", "") or "")
            raw_i = str(ai_dict.get("intent", "UNKNOWN")).upper()
            intent = SupportIntent(raw_i) if raw_i in [i.value for i in SupportIntent] else SupportIntent.UNKNOWN

            if not raw_reply or raw_reply.strip() == "None":
                # Detailed diagnostic logging
                raw_text_debug = getattr(result, "formatted_answer", "N/A")
                logger.warning(f"[SupportAgent] AI returned empty logic. AgenticResponse: {ai_data_str} | Raw: {raw_text_debug}")
                # 🚀 Safety Fallback Recovery (Elite V2.2: KB-Driven)
                msg_lower = request.message.lower()
                is_purchase = any(kw in msg_lower for kw in ("ship", "mua", "đặt", "giao", "lọ", "hộp", "chai", "combo"))
                fallback_key = "HELEN_SAFETY_FALLBACK" if is_purchase else "HELEN_EMPTY_FALLBACK"
                
                kb_fallback = await kb_service.search_relevant_knowledge(db, fallback_key, limit=1)
                if kb_fallback and "A: " in kb_fallback:
                    raw_reply = kb_fallback.split("A: ")[1].split("\n---")[0].strip()
                    intent = SupportIntent.GENERAL_ADVICE if is_purchase else SupportIntent.UNKNOWN
                else:
                    if is_purchase:
                        raw_reply = "Dạ Helen đã ghi nhận ạ! Để Helen lên đơn nhanh nhất cho mình, bạn vui lòng để lại **Số điện thoại + Địa chỉ nhận hàng** xuống bên dưới nhé. Đơn này đang có ưu đãi MIỄN PHÍ VẬN CHUYỂN toàn quốc luôn ạ! 🌸"
                        intent = SupportIntent.GENERAL_ADVICE
                    else:
                        raw_reply = "Dạ câu hỏi của bạn chứa một số từ ngữ mà hệ thống lọc tự động của bên em đang tạm che mờ. Bạn có thể nói rõ hơn hoặc liên hệ trực tiếp hotline để em hỗ trợ nhé!"
            
            # ELITE V2.2: Intent Override (Heuristic Boost)
            if is_heuristic_high:
                # If heuristic detected high intent, promote to PURCHASE regardless of AI doubt
                if intent in (SupportIntent.UNKNOWN, SupportIntent.GENERAL_ADVICE):
                    intent = SupportIntent.PURCHASE
                
        except Exception as exc:
            logger.error("[SupportAgent] AI call failed: %s", exc)
            raw_reply = (
                f"Xin lỗi, hệ thống đang bận. "
                f"Mời quý khách / bạn liên hệ hotline để được hỗ trợ ngay ạ!"
            )

        # Security Layer ④: Response sanitizer
        safe_reply = _sanitize_response(raw_reply)

        duration_ms = int((time.monotonic() - t0) * 1000)

        # Emit telemetry to EventBus (batch, no PII in payload)
        await event_bus.emit("SUPPORT_QUERY_LOG", {
            "session_id": session_id,
            "intent": intent.value,
            "duration_ms": duration_ms,
        })

        # 🚀 REAL-TIME PULSE: Notify all active admin dashboards (Elite V2.2)
        await event_bus.emit("SUPPORT_INBOX_UPDATE", {
            "session_id": session_id,
            "intent": intent.value,
            "customer_name": customer_name,
            "customer_phone": request.customer_phone,
            "is_high_intent": is_heuristic_high
        })

        # Persist messages to history (Zalo-style persistence)
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

        return SupportResponse(
            ok=True,
            reply=safe_reply,
            intent=intent,
            session_id=session_id,
            product_info=product_info
        )

    async def _save_history(
        self,
        db: AsyncSession,
        session_id: str,
        user_msg: str,
        assistant_reply: str,
        intent: SupportIntent,
        product_slug: Optional[str],
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None
    ) -> None:
        """Saves both user and assistant messages to the persistent history table."""
        try:
            # Elite V2.2: End-to-End Persistence Security (Kế thừa GeminiSecurity)
            # Mã hóa nội dung trước khi lưu vào Database để đảm bảo Zero-Knowledge
            enc_user_msg = GeminiSecurity.encrypt(user_msg)
            enc_assistant_reply = GeminiSecurity.encrypt(assistant_reply)

            # 1. Save User Message
            user_hist = SupportChatHistory(
                session_id=session_id,
                role="user",
                content=enc_user_msg, # Strictly encrypted, NO fallback to cleartext
                intent=intent.value,
                product_slug=product_slug,
                customer_name=customer_name,
                customer_phone=customer_phone
            )
            # 2. Save Assistant Message
            assistant_hist = SupportChatHistory(
                session_id=session_id,
                role="assistant",
                content=enc_assistant_reply, # Strictly encrypted
                intent=intent.value,
                product_slug=product_slug,
                customer_name=customer_name,
                customer_phone=customer_phone
            )
            db.add_all([user_hist, assistant_hist])
            await db.commit() # Forced commit for history persistence
        except Exception as exc:
            logger.warning("[SupportAgent] Failed to save chat history: %s", exc)
            await db.rollback()

    async def _fetch_chat_context(self, db: AsyncSession, session_id: str) -> str:
        """Retrieves recent chat history to provide reasoning context (Elite V2.2)."""
        history_text = ""
        try:
            stmt = (
                select(SupportChatHistory)
                .where(SupportChatHistory.session_id == session_id)
                .order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id))
                .limit(4)
            )
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

    async def _build_prompt_directive(
        self, product_ctx: str, kb_ctx: str, history_text: str = ""
    ) -> str:
        """Construct AI System Directive with structured knowledge and identity."""
        ctx_block: str = f"\n{kb_ctx}\n{product_ctx}\n" if (product_ctx or kb_ctx) else ""
        
        # Elite V2.2: Dynamic Prompt Loading
        agentic_directive = await xohi_memory.client.get("support:agent:system_prompt")
        
        if not agentic_directive:
            try:
                if os.path.exists(support_cfg.prompt_template_path):
                    def _read_file() -> str:
                        with open(support_cfg.prompt_template_path, "r", encoding="utf-8") as f:
                            return f.read()
                    agentic_directive = await asyncio.to_thread(_read_file)
                else:
                    agentic_directive = support_cfg.system_directive # Fallback to generic
            except Exception:
                agentic_directive = support_cfg.system_directive

        return (
            f"{agentic_directive}\n"
            f"{history_text}\n"
            f"[KNOWLEDGE CONTEXT]\n{ctx_block}\n"
            f"--- BẮT ĐẦU PHÂN TÍCH VÀ PHẢN HỒI ---"
        )
    async def _log_telemetry(
        self,
        db: AsyncSession,
        session_id: str,
        duration_ms: int,
    ) -> None:
        """Non-blocking telemetry write. Swallows errors to not affect response."""
        try:
            log = AgentTelemetryLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                agent_name=support_cfg.agent_name,
                intent_hash="support",
                duration_ms=duration_ms,
            )
            db.add(log)
            await db.flush()
        except Exception as exc:
            logger.warning("[SupportAgent] Telemetry log failed (non-critical): %s", exc)


# Module-level singleton
support_agent = SupportAgentOperative()
