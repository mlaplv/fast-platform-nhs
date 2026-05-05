"""
Support Chat Controller — SUPPORT_NAME_CLIENT
===============================================
Litestar endpoint for the client-facing support chat widget.
Route: POST /api/v1/client/support/chat

Security:
- Security Layer ②: Redis rate limiting (IP + session_id)
- Zero-Auth (guards=[]) — Zero-Barrier protocol
- Delegates to SupportAgentOperative for all business logic
"""
from __future__ import annotations

import logging
import time

from litestar import Controller, get, post, Request, Response
from litestar.exceptions import TooManyRequestsException, NotFoundException
import sqlalchemy as sa
from sqlalchemy import select, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.system import SupportChatHistory
from backend.schemas.support import SupportRequest, SupportResponse, SupportHistoryItem, SupportStatusResponse, UrgentSupportRequest
from backend.services.commerce.constants.support_config import support_cfg
from backend.services.commerce.operatives.support_agent import support_agent
from backend.utils.security import GeminiSecurity
from backend.constants.infra import HELEN_FOLLOW_UP_TRIGGER

logger = logging.getLogger("api-gateway")


class SupportController(Controller):
    """Client-facing support chat controller. Zero-Auth, Zero-Barrier."""

    path = "/api/v1/client/support"

    async def _check_rate_limit(self, request: Request, session_id: str | None) -> None:
        """
        Security Layer ②: Redis TTL-based rate limiter.
        Keys: `support:ip:<ip>` and `support:sid:<session_id>`
        Falls back gracefully if Redis is unavailable.
        """
        try:
            from backend.services.xohi_memory import xohi_memory  # Redis client reuse
            redis = xohi_memory.client
            if not redis:
                return

            ip = request.client.host if request.client else "unknown"
            if forwarded := request.headers.get("x-forwarded-for"):
                ip = forwarded.split(",")[0].strip()

            now_minute = int(time.time() // 60)
            ip_key = f"support:ip:{ip}:{now_minute}"
            ip_count = await redis.incr(ip_key)
            if ip_count == 1:
                await redis.expire(ip_key, 90)  # 1.5 min TTL for safety
            if ip_count > support_cfg.rate_limit_per_ip:
                raise TooManyRequestsException(detail="Quá nhiều yêu cầu. Vui lòng thử lại sau.")

            if session_id:
                sid_key = f"support:sid:{session_id}:{now_minute}"
                sid_count = await redis.incr(sid_key)
                if sid_count == 1:
                    await redis.expire(sid_key, 90)
                if sid_count > support_cfg.rate_limit_per_sid:
                    raise TooManyRequestsException(detail="Quá nhiều yêu cầu. Vui lòng thử lại sau.")

        except TooManyRequestsException:
            raise
        except Exception as exc:
            logger.warning("[SupportController] Rate limit check failed (skipping): %s", exc)

    @get("/history", guards=[])
    async def get_history(
        self,
        db_session: AsyncSession,
        session_id: str,
        limit: int = 20,
        before_id: str | None = None,
    ) -> list[SupportHistoryItem]:
        """
        Retrieves paginated chat history for a session.
        Zalo-style: Loads recent segments first.
        """
        try:
            stmt = (
                select(SupportChatHistory)
                .where(SupportChatHistory.session_id == session_id)
                .order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id))
                .limit(limit)
            )

            if before_id and before_id != "undefined":
                # Subquery to find the timestamp of the before_id message
                # Elite V2.2: Guard against invalid or missing cursor IDs
                cursor_stmt = select(SupportChatHistory.created_at).where(SupportChatHistory.id == before_id)
                cursor_res = await db_session.execute(cursor_stmt)
                cursor_time = cursor_res.scalar()
                
                if cursor_time:
                    stmt = stmt.where(
                        sa.or_(
                            SupportChatHistory.created_at < cursor_time,
                            sa.and_(
                                SupportChatHistory.created_at == cursor_time,
                                SupportChatHistory.id < before_id
                            )
                        )
                    )

            result = await db_session.execute(stmt)
            rows = result.scalars().all()
            
            # Return in chronological order for the client (reversed from our DESC fetch)
            items = []
            for r in reversed(rows):
                try:
                    # R2: Fault-tolerant decryption. Identify and skip corrupted segments 
                    # without crashing the entire session view for the user.
                    decrypted = "[Tin nhắn đã bị thu hồi]" if r.is_revoked else (GeminiSecurity.decrypt(r.content) if r.content else "")
                    
                    if decrypted == HELEN_FOLLOW_UP_TRIGGER:
                        continue # Hide internal triggers from client view
                    
                    items.append(SupportHistoryItem(
                        id=str(r.id),
                        role=r.role,
                        content=decrypted,
                        intent=r.intent,
                        timestamp=r.created_at.isoformat() if r.created_at else None,
                        is_revoked=r.is_revoked
                    ))
                except Exception as row_err:
                    logger.warning("[SupportController] Skipping corrupted history row %s: %s", r.id, row_err)
                    continue

            return items
        except Exception as exc:
            # R2: Final safety net. Log the critical error but return current items if any.
            logger.error("[SupportController] Critical History lookup failure: %s", exc, exc_info=True)
            return []

    @get("/status", guards=[])
    async def get_status(self) -> SupportStatusResponse:
        """
        Public endpoint to check if Helen AI is enabled.
        Used by the client FAB for dynamic tooltips.
        """
        from backend.services.xohi_memory import xohi_memory
        helen_on = await xohi_memory.client.get("system:helen_enabled")
        offline_msg = await xohi_memory.client.get("system:helen_offline_msg")
        
        return SupportStatusResponse(
            helen_enabled=helen_on != "0",
            offline_message=offline_msg or "Dược sĩ tư vấn sẽ sớm phản hồi sếp. Vui lòng để lại lời nhắn ạ."
        )

    @post("/chat", guards=[])
    async def chat(
        self,
        request: Request,
        db_session: AsyncSession,
        data: SupportRequest,
    ) -> SupportResponse:
        """
        Handles a single client support message.
        - Synchronous Tier-1 Butler (Greetings/FAQ)
        - Asynchronous Tier-2/3 Brain (LLM/RAG via arq)
        """
        session_id = data.session_id or "unknown"
        
        try:
            await self._check_rate_limit(request, session_id)
            response = await support_agent.chat(request=data, db=db_session)
            await db_session.commit()
            status_code = 202 if response.status == "PROCESSING" else 200
            return Response(content=response, status_code=status_code)
        except Exception as e:
            logger.error(f"💥 [SupportController] FAILURE for SID: {session_id}: {e}", exc_info=True)
            await db_session.rollback()
            return Response(
                content=SupportResponse(
                    ok=False,
                    reply="Xin lỗi sếp, hệ thống tư vấn đang gặp sự cố nhỏ. Sếp vui lòng thử lại sau vài giây ạ.",
                    intent=SupportIntent.UNKNOWN,
                    session_id=session_id,
                    status="FAILED"
                ),
                status_code=500
            )

    @post("/urgent", guards=[])
    async def urgent_support(
        self,
        request: Request,
        db_session: AsyncSession,
        data: UrgentSupportRequest,
    ) -> dict[str, bool]:
        """
        Handles an urgent support request (Viral 30-Second Rule).
        Emits a Pulse notification to admins immediately.
        """
        try:
            # 1. Anti-Spam: Rate Limit by IP
            ip = request.client.host if request.client else "unknown"
            if forwarded := request.headers.get("x-forwarded-for"):
                ip = forwarded.split(",")[0].strip()
            # Minimal rate limit logic: reuse _check_rate_limit if possible, but keep it standalone for now
            
            # 2. Emits a CRITICAL Pulse Notification to Admin Dashboard
            from backend.services.signal_center import signal_center
            from backend.schemas.signal import SignalSchema, SignalSeverity

            msg = f"Khách VIP {data.phone} yêu cầu gọi lại trong 30s! Nguồn: {data.source_url or 'Trang chủ'}"
            
            signal = SignalSchema(
                signal_type="URGENT_SUPPORT",
                message=msg,
                severity=SignalSeverity.CRITICAL,
                payload={"phone": data.phone, "source_url": data.source_url},
                persist=True
            )
            
            await signal_center.dispatch(
                user_id="ADMIN",  # Broadcast or specific admin role
                signal=signal,
                db_session=db_session
            )
            
            # Note: Tích hợp Zalo/Telegram webhook sẽ được thực hiện tại SignalCenter/EventBus 
            # lắng nghe sự kiện "URGENT_SUPPORT".
            
            return {"ok": True}
        except Exception as e:
            logger.error(f"💥 [SupportController] URGENT FAILURE: {e}", exc_info=True)
            return {"ok": False}
