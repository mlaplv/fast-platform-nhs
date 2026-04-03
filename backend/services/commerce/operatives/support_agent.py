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

import logging
import time
import uuid
from typing import Optional

from pydantic_ai import Agent
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.commerce import ProductBase
from backend.database.models.content import Category
from backend.database.models.system import AgentTelemetryLog, SupportChatHistory
from backend.schemas.support import SupportIntent, SupportRequest, SupportResponse, SupportProductInfo
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
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
# PYDANTIC AI AGENT — Singleton, initialized once at module load
# ══════════════════════════════════════════════════════════════
_support_ai_agent: Agent[None, str] = Agent(
    output_type=str,
    retries=2,
)

# ══════════════════════════════════════════════════════════════
# INTENT CLASSIFIER — Heuristic, zero AI cost for simple cases
# ══════════════════════════════════════════════════════════════
_ESCALATE_SIGNALS = ("khiếu nại", "complaint", "tức", "bực", "hoàn tiền", "refund", "tệ", "tồi")
_ORDER_SIGNALS    = ("đơn hàng", "đơn của tôi", "vận chuyển", "giao hàng", "tracking", "ship", "order")
_POLICY_SIGNALS   = ("chính sách", "bảo hành", "đổi trả", "hoàn hàng", "warranty", "return")
_PRICE_SIGNALS    = ("giá", "price", "bao nhiêu", "combo", "ưu đãi", "khuyến mãi", "discount")


def _classify_intent(message: str) -> SupportIntent:
    """Fast heuristic intent classifier — O(n) keyword scan, no AI required."""
    msg = message.lower()
    if any(k in msg for k in _ESCALATE_SIGNALS):
        return SupportIntent.ESCALATE
    if any(k in msg for k in _ORDER_SIGNALS):
        return SupportIntent.ORDER_STATUS
    if any(k in msg for k in _POLICY_SIGNALS):
        return SupportIntent.POLICY_QUERY
    if any(k in msg for k in _PRICE_SIGNALS):
        return SupportIntent.PRICE_QUERY
    return SupportIntent.GENERAL_ADVICE


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
            parts = [
                f"Mua {d.get('buy_qty', 0)} tặng {d.get('get_qty', 0)}: {float(d.get('fixed_price', 0)):,.0f}đ"
                for d in deals_raw if d.get("buy_qty")
            ]
            deals_text = f"\nCHƯƠNG TRÌNH ƯU ĐÃI: {'; '.join(parts)}" if parts else ""

        context = (
            f"[THÔNG TIN SẢN PHẨM HIỆN TẠI]\n"
            f"Tên: {row.name}\n"
            f"Danh mục: {row.category_name or 'Chưa phân loại'}\n"
            f"Giá: {price_display}{deals_text}\n"
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
    import re
    # Strip any SUPPORT_SYSTEM_DIRECTIVE fragments that may have leaked
    dangerous_patterns = [
        r"TUYỆT ĐỐI không tiết lộ",
        r"/backend[/\w]*",
        r"api[_-]?key\s*[:=]\s*\S+",
        r"sk-[A-Za-z0-9]{10,}",
        r"Traceback \(most recent",
    ]
    for pat in dangerous_patterns:
        raw = re.sub(pat, "", raw, flags=re.IGNORECASE)

    # Soft word-count cap (not token, but safe approximation)
    words = raw.split()
    limit_idx: int = int(support_cfg.max_response_tokens)
    if len(words) > limit_idx:
        raw = " ".join(words[:limit_idx]) + "..."

    return raw.strip()


# ══════════════════════════════════════════════════════════════
# MAIN OPERATIVE CLASS
# ══════════════════════════════════════════════════════════════

class SupportAgentOperative:
    """
    Client-facing chat operative. Handles intent routing, product RAG,
    and safe AI response generation for SUPPORT_NAME_CLIENT.
    """

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

        # ELITE V2.2: Global Helen Toggle Check (Redis-cached)
        helen_on = await xohi_memory.client.get("system:helen_enabled")
        if helen_on == "0":
            offline_msg = await xohi_memory.client.get("system:helen_offline_msg")
            reply = offline_msg or "Hiện tại em Helen đang được bảo trì, tư vấn viên sẽ hỗ trợ sếp ngay ạ!"
            
            # 🚀 QUANTUM BRIDGE: Push to Zalo OA when Helen is OFF
            customer_name = request.customer_name or "Khách ẩn danh"
            await zalo_service.push_support_notification(
                customer_name=customer_name,
                message=request.message,
                session_id=session_id
            )

            # Vẫn lưu lịch sử để nhân viên vào xem được thưa sếp!
            await self._save_history(
                db,
                session_id=session_id,
                user_msg=request.message,
                assistant_reply=reply,
                intent=SupportIntent.GENERAL_ADVICE,
                product_slug=request.product_slug
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

        # Heuristic intent classification (no AI cost)
        intent = _classify_intent(request.message)

        # Hard-scripted responses for non-AI intents (fast path)
        scripted = self._get_scripted_response(intent, session_id)
        if scripted:
            return scripted

        # Build RAG context from knowledge base (Elite V2.2: Structured Tri thức)
        kb_repo = SupportKnowledgeRepository(session=db)
        kb_service = SupportKnowledgeService(repo=kb_repo)
        kb_ctx = await kb_service.search_relevant_knowledge(db, request.message)

        # Fetch history for context restoration (Elite V2.2: Context Pulse)
        from sqlalchemy import desc
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
                    h_content = (GeminiSecurity.decrypt_keys(r.content) or [""])[0] if r.content else ""
                    h_role = "Khách" if r.role == "user" else "Helen"
                    h_parts.append(f"{h_role}: {h_content}")
                history_text = "\n[LỊCH SỬ GẦN ĐÂY]\n" + "\n".join(h_parts) + "\n"
        except Exception as h_exc:
            logger.warning("[SupportAgent] Context retrieval failed: %s", h_exc)

        # Build RAG context from product (read-only DB)
        product_ctx, product_info = await _fetch_product_context(db, request.product_slug)

        # Construct prompt with system directive from env
        prompt = self._build_prompt(request.message, product_ctx, kb_ctx, intent, history_text)

        # Run AI via TrinityBridge (role="fast" → flash models)
        try:
            result = await trinity_bridge.run(
                _support_ai_agent,
                prompt,
                role=support_cfg.model_role,
                system_prompt=support_cfg.system_directive,
            )
            # ELITE: Handle PydanticAI Result without explicit import to avoid version mismatch
            res_data = getattr(result, "data", None)
            if res_data:
                raw_reply = str(res_data)
            elif hasattr(result, "all_messages"):
                # Fallback to message history if structured data is missing
                msgs = getattr(result, "all_messages")() 
                if msgs:
                    last_msg = msgs[-1]
                    if hasattr(last_msg, "parts") and last_msg.parts:
                        part = last_msg.parts[0]
                        raw_reply = str(getattr(part, "content", part))
                    else:
                        raw_reply = str(getattr(last_msg, "content", last_msg))
                else:
                    raw_reply = ""
            else:
                raw_reply = ""
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

        # Persist messages to history (Zalo-style persistence)
        await self._save_history(
            db,
            session_id=session_id,
            user_msg=request.message,
            assistant_reply=safe_reply,
            intent=intent,
            product_slug=request.product_slug
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
        product_slug: Optional[str]
    ) -> None:
        """Saves both user and assistant messages to the persistent history table."""
        try:
            # Elite V2.2: End-to-End Persistence Security (Kế thừa GeminiSecurity)
            # Mã hóa nội dung trước khi lưu vào Database để đảm bảo Zero-Knowledge
            enc_user_msg = GeminiSecurity.encrypt_keys([user_msg])
            enc_assistant_reply = GeminiSecurity.encrypt_keys([assistant_reply])

            # 1. Save User Message
            user_hist = SupportChatHistory(
                session_id=session_id,
                role="user",
                content=enc_user_msg, # Strictly encrypted, NO fallback to cleartext
                intent=intent.value,
                product_slug=product_slug
            )
            # 2. Save Assistant Message
            assistant_hist = SupportChatHistory(
                session_id=session_id,
                role="assistant",
                content=enc_assistant_reply, # Strictly encrypted
                intent=intent.value,
                product_slug=product_slug
            )
            db.add_all([user_hist, assistant_hist])
            await db.commit() # Forced commit for history persistence
        except Exception as exc:
            logger.warning("[SupportAgent] Failed to save chat history: %s", exc)
            await db.rollback()

    def _get_scripted_response(
        self, intent: SupportIntent, session_id: str
    ) -> Optional[SupportResponse]:
        """Return pre-scripted response for high-certainty intents (no AI needed)."""
        if intent == SupportIntent.ORDER_STATUS:
            return SupportResponse(
                ok=True,
                reply=(
                    "Để kiểm tra đơn hàng, bạn vui lòng liên hệ hotline hoặc "
                    "nhắn tin Zalo của shop để được hỗ trợ nhanh nhất nhé! "
                    "Em không có quyền truy cập thông tin đơn hàng riêng tư của bạn."
                ),
                intent=intent,
                session_id=session_id,
            )
        if intent == SupportIntent.ESCALATE:
            return SupportResponse(
                ok=True,
                reply=(
                    "Em rất tiếc về trải nghiệm của bạn. Để được giải quyết nhanh nhất, "
                    "vui lòng liên hệ trực tiếp qua hotline hoặc Zalo shop. "
                    "Đội ngũ chăm sóc khách hàng sẽ hỗ trợ bạn trong thời gian sớm nhất!"
                ),
                intent=intent,
                session_id=session_id,
            )
        return None

    def _build_prompt(
        self, message: str, product_ctx: str, kb_ctx: str, intent: SupportIntent, history_text: str = ""
    ) -> str:
        """Construct AI prompt with optional RAG context injection."""
        ctx_block = f"\n{kb_ctx}\n{product_ctx}\n" if (product_ctx or kb_ctx) else ""
        intent_hint = f"[Phân loại câu hỏi: {intent.value}]\n" if intent else ""
        return f"{intent_hint}{history_text}{ctx_block}Câu hỏi của khách: {message}"

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
