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

from litestar import Controller, post, Request
from litestar.exceptions import TooManyRequestsException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.read_session import provide_read_only_db
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

    @post("/chat", guards=[])
    async def chat(
        self,
        request: Request,
        data: SupportRequest,
    ) -> SupportResponse:
        """
        Handles a single client support message.
        - Zero-Auth public endpoint (guards=[])
        - Rate limited per IP and session_id
        - Delegates all AI + security logic to SupportAgentOperative
        """
        await self._check_rate_limit(request, data.session_id)

        # Instantiate read-only session manually (not via DI to avoid write-capable session)
        async for db in provide_read_only_db():
            return await support_agent.chat(request=data, db=db)

        # Fallback (unreachable but makes type checker happy)
        raise RuntimeError("Support agent could not obtain a database session.")
