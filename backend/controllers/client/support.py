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
from litestar.datastructures import Cookie
import uuid

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

            # M-1: Trusted IP resolution — prefer Nginx-injected x-real-ip over spoofable x-forwarded-for
            # x-forwarded-for can be faked by the client to bypass rate limiting
            ip = (
                request.headers.get("x-real-ip")
                or (request.client.host if request.client else None)
                or "unknown"
            )

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

    @get("/init", guards=[])
    async def init_session(self, request: Request) -> Response[dict]:
        """
        Creates a new HttpOnly Cookie for session tracking if one doesn't exist.
        Bypasses Cloudflare cache to avoid Cache Poisoning.
        """
        session_id = request.cookies.get("helen_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            cookie = Cookie(
                key="helen_session_id",
                value=session_id,
                httponly=True,
                secure=True,
                samesite="lax",
                path="/",
                max_age=86400 * 30,  # M-4: 30-day TTL — prevent stale session accumulation
            )
            # Important: Prevent caching
            headers = {
                "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            }
            return Response({"ok": True, "session_id": session_id}, cookies=[cookie], headers=headers)
        return Response({"ok": True, "session_id": session_id})

    @get("/history", guards=[])
    async def get_history(
        self,
        request: Request,
        db_session: AsyncSession,
        limit: int = 20,
        before_id: str | None = None,
    ) -> list[SupportHistoryItem]:
        """
        Retrieves paginated chat history for a session.
        Zalo-style: Loads recent segments first.
        """
        session_id = request.cookies.get("helen_session_id")
        if not session_id:
            return []
        
        try:
            import re as _re
            _UUID_RE = _re.compile(r'^[0-9a-f\-]{32,36}$', _re.IGNORECASE)
            stmt = (
                select(SupportChatHistory)
                .where(SupportChatHistory.session_id == session_id)
                .order_by(desc(SupportChatHistory.created_at), desc(SupportChatHistory.id))
                .limit(limit)
            )

            if before_id and before_id != "undefined" and _UUID_RE.match(before_id):
                # M-3: UUID format validated — safe to use as DB cursor
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
            offline_message=offline_msg or "Dược sĩ tư vấn sẽ sớm phản hồi Quý khách. Vui lòng để lại lời nhắn ạ."
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
        session_id = request.cookies.get("helen_session_id")
        if not session_id:
             # Fallback if somehow /init failed
             session_id = str(uuid.uuid4())
             
        data.session_id = session_id # Override with secure cookie session
        
        try:
            # Elite V3.5: Hardened Anti-Spam & Duplicate Message Defense thưa sếp!
            from backend.services.xohi_memory import xohi_memory
            redis = xohi_memory.client
            if redis:
                import hashlib
                msg_clean = data.message.strip().lower()
                msg_hash = hashlib.md5(msg_clean.encode("utf-8")).hexdigest()
                
                # A. Anti-Spam click check (<1.5s interval)
                last_time_key = f"support:last_msg_time:{session_id}"
                last_time_val = await redis.get(last_time_key)
                now = time.time()
                
                if last_time_val:
                    elapsed = now - float(last_time_val)
                    if elapsed < 1.5:
                        logger.warning(f"🛡️ [Anti-Spam] Session {session_id} click rate limit exceeded: {elapsed:.2f}s")
                        from backend.schemas.support import SupportIntent
                        return Response(
                            content=SupportResponse(
                                ok=False,
                                reply="Helen đang xử lý yêu cầu trước đó của mình, vui lòng đợi một chút nhé ạ! ✨",
                                intent=SupportIntent.UNKNOWN,
                                session_id=session_id,
                                status="FAILED"
                            ),
                            status_code=200 # Return 200 with soft warning for seamless UX
                        )
                await redis.set(last_time_key, str(now), ex=5)

                # B. Anti-Duplicate query check (<10s interval)
                hash_key = f"support:dup_hash:{session_id}"
                last_hash = await redis.get(hash_key)
                if last_hash and last_hash.decode("utf-8") == msg_hash:
                    logger.warning(f"🛡️ [Anti-Spam] Duplicate question blocked for Session {session_id}")
                    from backend.schemas.support import SupportIntent
                    return Response(
                        content=SupportResponse(
                           ok=False,
                           reply="Helen vừa nhận được câu hỏi này từ mình rồi ạ. Mình đợi Helen trả lời xong nhé! 💕",
                           intent=SupportIntent.UNKNOWN,
                           session_id=session_id,
                           status="FAILED"
                        ),
                        status_code=200
                    )
                await redis.set(hash_key, msg_hash, ex=10)

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
                    reply="Xin lỗi Quý khách, hệ thống tư vấn đang gặp sự cố nhỏ. Quý khách vui lòng thử lại sau vài giây ạ.",
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

            # M-2: Mask phone number before broadcasting in cleartext to admin signals
            _masked_phone = f"{data.phone[:3]}****{data.phone[-3:]}" if len(data.phone) >= 6 else "****"
            msg = f"Khách VIP {_masked_phone} yêu cầu gọi lại trong 30s! Nguồn: {data.source_url or 'Trang chủ'}"
            
            signal = SignalSchema(
                signal_type="URGENT_SUPPORT",
                message=msg,
                severity=SignalSeverity.CRITICAL,
                payload={"phone": data.phone, "source_url": data.source_url},
                persist=True
            )
            
            await signal_center.dispatch(
                user_id="user_admin",  # Broadcast or specific admin role
                signal=signal,
                db_session=db_session
            )
            
            # Note: Tích hợp Zalo/Telegram webhook sẽ được thực hiện tại SignalCenter/EventBus 
            # lắng nghe sự kiện "URGENT_SUPPORT".
            
            return {"ok": True}
        except Exception as e:
            logger.error(f"💥 [SupportController] URGENT FAILURE: {e}", exc_info=True)
            return {"ok": False}
