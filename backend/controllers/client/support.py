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

from litestar import Controller, get, post, Request
from litestar.exceptions import TooManyRequestsException, NotFoundException
import sqlalchemy as sa
from sqlalchemy import select, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models.system import SupportChatHistory
from backend.schemas.support import SupportRequest, SupportResponse
from backend.services.commerce.constants.support_config import support_cfg
from backend.services.commerce.operatives.support_agent import support_agent

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
    ) -> list[dict]:
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
            return [
                {
                    "id": r.id,
                    "role": r.role,
                    "content": r.content,
                    "intent": r.intent,
                    "timestamp": r.created_at.isoformat() if r.created_at else None
                }
                for r in reversed(rows)
            ]
        except Exception as exc:
            # R2: Silent fail for non-critical history lookup to protect availability
            logger.error("[SupportController] History lookup failed: %s", exc)
            return []

    @get("/status", guards=[])
    async def get_status(self) -> dict:
        """
        Public endpoint to check if Helen AI is enabled.
        Used by the client FAB for dynamic tooltips.
        """
        from backend.services.xohi_memory import xohi_memory
        helen_on = await xohi_memory.client.get("system:helen_enabled")
        offline_msg = await xohi_memory.client.get("system:helen_offline_msg")
        
        return {
            "helen_enabled": helen_on != "0",
            "offline_message": offline_msg or "Dược sĩ tư vấn sẽ sớm phản hồi sếp. Vui lòng để lại lời nhắn ạ."
        }

    @post("/chat", guards=[])
    async def chat(
        self,
        request: Request,
        db_session: AsyncSession,
        data: SupportRequest,
    ) -> SupportResponse:
        """
        Handles a single client support message.
        - Zero-Auth public endpoint (guards=[])
        - Rate limited per IP and session_id
        - Uses writeable session for history persistence
        """
        await self._check_rate_limit(request, data.session_id)

        return await support_agent.chat(request=data, db=db_session)
