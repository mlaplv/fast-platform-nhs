"""
Context Guard — Stateful Multi-turn Prompt Injection Blocker
=============================================================
Elite V2.2: Chặn kỹ thuật chia nhỏ hướng dẫn độc hại qua nhiều câu chat liên tiếp.
Design: Lưu N tin nhắn gần nhất trong Redis, ghép lại để kiểm tra pattern.
"""
from __future__ import annotations

import logging
from typing import Final, Optional

logger = logging.getLogger("api-gateway")

_MAX_CTX_MESSAGES: Final[int] = 3
_CTX_TTL_SECONDS: Final[int] = 600       # 10 phút rolling window
_CTX_KEY_PREFIX: Final[str] = "support:ctx_guard:"
_SEPARATOR: Final[str] = " ||| "         # Phân tách tin nhắn khi ghép


def _redis():  # type: ignore[return]
    """Lazy-load Redis client — tránh circular import."""
    try:
        from backend.services.xohi_memory import xohi_memory
        return xohi_memory.client
    except Exception:
        return None


async def record_message(session_id: str, message: str) -> None:
    """
    Lưu tin nhắn mới vào sliding window (tối đa _MAX_CTX_MESSAGES).
    Dùng LPUSH + LTRIM — atomic, O(1).
    Không raise exception — fail silently để không ảnh hưởng UX.
    """
    r = _redis()
    if not r or not message:
        return
    try:
        key: str = f"{_CTX_KEY_PREFIX}{session_id}"
        async with r.pipeline(transaction=False) as pipe:
            pipe.lpush(key, message[:500])           # Giới hạn 500 ký tự/message để tránh RAM spike
            pipe.ltrim(key, 0, _MAX_CTX_MESSAGES - 1)
            pipe.expire(key, _CTX_TTL_SECONDS)
            await pipe.execute()
    except Exception as e:
        logger.debug("[ContextGuard] record_message failed (silent): %s", e)


async def check_session_threat(session_id: str, new_message: str) -> tuple[bool, str | None]:
    """
    Ghép N tin nhắn gần nhất + tin nhắn mới, kiểm tra pattern injection.
    Returns (is_safe, reason).
    - is_safe=True  → session sạch, tiếp tục xử lý.
    - is_safe=False → phát hiện injection tích lũy, reject.
    Fail-open: nếu Redis/InputGuard lỗi → trả về (True, None).
    """
    r = _redis()
    if not r:
        return True, None

    try:
        key: str = f"{_CTX_KEY_PREFIX}{session_id}"
        history: list[str] = await r.lrange(key, 0, _MAX_CTX_MESSAGES - 1)
    except Exception as e:
        logger.debug("[ContextGuard] lrange failed (fail-open): %s", e)
        return True, None

    # Ghép: oldest → newest → new_message
    ordered: list[str] = list(reversed(history)) + [new_message]
    combined: str = _SEPARATOR.join(ordered)

    try:
        from backend.services.commerce.security.input_guard import InputGuard
        is_safe, reason = InputGuard.validate(combined)
        if not is_safe:
            logger.warning(
                "[ContextGuard] Multi-turn injection detected. Session=%s Reason=%s Combined(80)=%.80s",
                session_id[:16], reason, combined,
            )
            return False, reason
    except Exception as e:
        logger.warning("[ContextGuard] InputGuard.validate failed (fail-open): %s", e)

    return True, None


async def clear_session(session_id: str) -> None:
    """Xoá context guard khi session kết thúc hoặc order hoàn thành."""
    r = _redis()
    if not r:
        return
    try:
        await r.delete(f"{_CTX_KEY_PREFIX}{session_id}")
    except Exception as e:
        logger.debug("[ContextGuard] clear_session failed: %s", e)
