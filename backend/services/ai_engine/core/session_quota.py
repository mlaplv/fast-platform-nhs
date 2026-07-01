"""
Session Quota Guard — Token Bucket per Session
=================================================
Elite V2.2: Giới hạn token LLM tiêu thụ theo session để chặn botnet đốt quota API.
Design: Redis Hash per session_id, sliding 1-hour window.
"""
from __future__ import annotations

import logging
import os
from typing import Final, Optional

logger = logging.getLogger("api-gateway")

# ── Cấu hình — đọc từ ENV để dễ điều chỉnh không cần deploy lại ──────────────
_HOURLY_INPUT_LIMIT: Final[int] = int(os.getenv("SESSION_INPUT_TOKEN_LIMIT", "50000"))
_HOURLY_OUTPUT_LIMIT: Final[int] = int(os.getenv("SESSION_OUTPUT_TOKEN_LIMIT", "10000"))
_QUOTA_WINDOW: Final[int] = 3600          # 1 giờ (giây)
_QUOTA_KEY_PREFIX: Final[str] = "ai:session:quota:"
_FIELD_INPUT: Final[str] = "input_tokens"
_FIELD_OUTPUT: Final[str] = "output_tokens"


class SessionQuotaGuard:
    """
    Token Bucket per session_id.
    Thread-safe thông qua Redis HINCRBY atomic.
    Singleton — khởi tạo 1 lần qua module-level instance.
    """

    _instance: Optional["SessionQuotaGuard"] = None

    def __new__(cls) -> "SessionQuotaGuard":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def _redis(self):  # type: ignore[return]
        """Lazy-load Redis client từ xohi_memory singleton."""
        try:
            from backend.services.xohi_memory import xohi_memory
            return xohi_memory.client
        except Exception:
            return None

    def _key(self, session_id: str) -> str:
        return f"{_QUOTA_KEY_PREFIX}{session_id}"

    async def check(self, session_id: str, estimated_input: int = 500) -> bool:
        """
        Kiểm tra session còn trong quota không.
        Returns True nếu ĐƯỢC PHÉP, False nếu HẾT QUOTA.
        Không block — fail-open nếu Redis không khả dụng.
        """
        r = self._redis()
        if not r:
            return True  # Fail-open: không chặn nếu Redis mất kết nối

        try:
            raw: Optional[str] = await r.hget(self._key(session_id), _FIELD_INPUT)
            current_input: int = int(raw) if raw else 0
            if current_input + estimated_input > _HOURLY_INPUT_LIMIT:
                logger.warning(
                    "[SessionQuota] Input limit reached: session=%s used=%d limit=%d",
                    session_id[:16], current_input, _HOURLY_INPUT_LIMIT,
                )
                return False
        except Exception as e:
            logger.debug("[SessionQuota] check failed (fail-open): %s", e)

        return True

    async def track(
        self,
        session_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Ghi nhận số token đã dùng sau khi LLM trả về thành công.
        Dùng pipeline để atomic — 1 round-trip duy nhất.
        """
        if input_tokens <= 0 and output_tokens <= 0:
            return

        r = self._redis()
        if not r:
            return

        try:
            key: str = self._key(session_id)
            async with r.pipeline(transaction=False) as pipe:
                if input_tokens > 0:
                    pipe.hincrby(key, _FIELD_INPUT, input_tokens)
                if output_tokens > 0:
                    pipe.hincrby(key, _FIELD_OUTPUT, output_tokens)
                # Refresh TTL mỗi lần có hoạt động (sliding window)
                pipe.expire(key, _QUOTA_WINDOW)
                await pipe.execute()
        except Exception as e:
            logger.debug("[SessionQuota] track failed: %s", e)

    async def get_usage(self, session_id: str) -> dict[str, int]:
        """Lấy số token đã dùng của session (dùng cho admin debug)."""
        r = self._redis()
        if not r:
            return {_FIELD_INPUT: 0, _FIELD_OUTPUT: 0}
        try:
            data: dict[str, str] = await r.hgetall(self._key(session_id))
            return {
                _FIELD_INPUT: int(data.get(_FIELD_INPUT, 0)),
                _FIELD_OUTPUT: int(data.get(_FIELD_OUTPUT, 0)),
            }
        except Exception:
            return {_FIELD_INPUT: 0, _FIELD_OUTPUT: 0}

    async def reset(self, session_id: str) -> None:
        """Xoá quota của session (dùng khi session xác thực là legitimate)."""
        r = self._redis()
        if not r:
            return
        try:
            await r.delete(self._key(session_id))
        except Exception as e:
            logger.debug("[SessionQuota] reset failed: %s", e)


# Module-level singleton — safe to import anywhere
session_quota: SessionQuotaGuard = SessionQuotaGuard()
