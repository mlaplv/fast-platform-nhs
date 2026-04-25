"""
[CNS V90.0] Shared Search Cache — Elite V2.2
Mục tiêu: Tái sử dụng kết quả Google Custom Search cho cùng keyword trong 30 phút.
Copyright + SEO cùng keyword → chỉ gọi Google 1 lần thay vì 2 lần.
"""
import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger("api-gateway")

# TTL 30 phút — đủ cho 1 phiên làm việc
_CACHE_TTL_SECONDS = 1800
# Max entries in-process cache (tránh OOM với 2GB RAM)
_MAX_CACHE_SIZE = 100

# ──────────────────────────────────────────────────────────────────────────────
# IN-PROCESS CACHE (Level 1: Fastest — cùng process lifecycle)
# Redis không cần thiết ở đây vì TTL ngắn và data chỉ cần per-worker
# ──────────────────────────────────────────────────────────────────────────────
_cache: dict[str, tuple[list[str], float]] = {}  # key → (snippets, expire_at)
_inflight: dict[str, asyncio.Event] = {}           # key → event (dedup concurrent requests)
_cache_lock = asyncio.Lock()


def _make_key(query: str, num: int) -> str:
    """Normalize query thành cache key."""
    return f"{query.lower().strip()}::{num}"


async def get_or_fetch(
    query: str,
    fetch_fn,  # Callable: async () -> list[str]
    num: int = 5,
    ttl: int = _CACHE_TTL_SECONDS,
) -> list[str]:
    """
    [CNS V90.0] Shared Cache với deduplication cho concurrent requests.
    """
    key = _make_key(query, num)
    now = time.monotonic()

    # ── Level 1: Cache HIT ────────────────────────────────────────────────────
    async with _cache_lock:
        entry = _cache.get(key)
        if entry:
            snippets, expire_at = entry
            if now < expire_at:
                logger.info(f"[SharedSearchCache] CACHE HIT (TTL còn {expire_at - now:.0f}s): '{query[:40]}'")
                return snippets
            else:
                del _cache[key]

        # ── Deduplication: concurrent request cho cùng key ───────────────────
        if key in _inflight:
            event = _inflight[key]
            is_fetcher = False
        else:
            event = asyncio.Event()
            _inflight[key] = event
            is_fetcher = True

    if not is_fetcher:
        # Waiting on concurrent fetch — poll until event set
        logger.info(f"[SharedSearchCache] DEDUP WAIT for: '{query[:40]}'")
        await event.wait()

        # Read from cache (should be available now)
        async with _cache_lock:
            entry = _cache.get(key)
        return entry[0] if entry else []

    # Nếu đây là request đầu tiên (fetcher)
    try:
        logger.info(f"[SharedSearchCache] CACHE MISS — Fetching Google for: '{query[:40]}'")
        results = await fetch_fn()
    except Exception as e:
        logger.error(f"[SharedSearchCache] Fetch failed: {e}")
        results = []

    # Ghi vào cache + signal waiting requests
    async with _cache_lock:
        # Enforce size limit
        if len(_cache) >= _MAX_CACHE_SIZE:
            oldest_key = min(_cache, key=lambda k: _cache[k][1])
            del _cache[oldest_key]

        _cache[key] = (results, now + ttl)
        _inflight.pop(key, None)
        event.set()

    return results


def invalidate(query: str, num: int = 5) -> None:
    """Force invalidate a cache entry (dùng khi content thay đổi hoàn toàn)."""
    key = _make_key(query, num)
    _cache.pop(key, None)
    logger.info(f"[SharedSearchCache] Invalidated: '{query[:40]}'")


def get_stats() -> dict:
    """Debug: trả về thống kê cache hiện tại."""
    now = time.monotonic()
    active = {k: round(v[1] - now, 1) for k, v in _cache.items() if v[1] > now}
    return {"active_entries": len(active), "inflight": len(_inflight), "entries": active}
