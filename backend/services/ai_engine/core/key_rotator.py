import os
import logging
import redis.asyncio as redis
from typing import Optional

logger = logging.getLogger("api-gateway")

class SmartKeyRotator:
    """
    R101/R106: Intelligent Key Management for LLM Tiers.
    V65.0: Singleton, fixed round-robin, auth cooldown, proper logging.
    """
    SUCCESS_INDEX_KEY = "ai:key_rotator:last_success_index"
    ROUND_ROBIN_KEY = "ai:key_rotator:round_robin_counter"
    STICKY_PREFIX = "ai:key_rotator:sticky:"
    UNHEALTHY_PREFIX = "ai:key_rotator:unhealthy:"

    # Cooldown durations
    COOLDOWN_MINUTE = 60      # Rate Limit (RPM)
    COOLDOWN_AUTH = 3600      # Invalid/revoked key - 1 hour
    COOLDOWN_DAILY = 86400    # Quota Exhausted (RPD) - 24 hours

    _instance: Optional["SmartKeyRotator"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        raw_keys = os.getenv("GEMINI_API_KEY", "")
        self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self.index = 0
        self._use_redis = False
        self.client = None

        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self._use_redis = True
            logger.info(f"[KeyRotator] Connected to Redis for shared state. Keys loaded: {len(self.keys)}")
        except Exception as e:
            logger.warning(f"[KeyRotator] Redis unavailable, using local memory: {e}")

        if not self.keys:
            logger.warning("[KeyRotator] No GEMINI_API_KEY found in environment!")

    async def get_key(self, session_id: Optional[str] = None) -> str:
        """
        Returns the best key to use.
        Prioritizes 'Sticky' key for the session, or global successful index.
        """
        if not self.keys: return ""

        num_keys = len(self.keys)
        start_index = self.index

        # 1. Attempt to get Sticky Key for this session
        if session_id and self._use_redis:
            try:
                sticky_idx = await self.client.get(f"{self.STICKY_PREFIX}{session_id}")
                if sticky_idx is not None:
                    start_index = int(sticky_idx) % num_keys
                else:
                    # No sticky index yet? Use hash-based stable routing
                    import hashlib
                    hash_val = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
                    start_index = hash_val % num_keys
            except Exception as e:
                logger.debug(f"[KeyRotator] Redis sticky lookup failed for session {session_id}: {e}")
        elif self._use_redis:
            # Global round-robin for anonymous sessions (separate from success index)
            try:
                global_idx = await self.client.incr(self.ROUND_ROBIN_KEY)
                start_index = global_idx % num_keys
            except Exception as e:
                logger.debug(f"[KeyRotator] Redis round-robin failed: {e}")

        # 2. Iterate through keys starting from the best candidate
        for i in range(num_keys):
            current_idx = (start_index + i) % num_keys
            key = self.keys[current_idx]

            if self._use_redis:
                try:
                    is_unhealthy = await self.client.get(f"{self.UNHEALTHY_PREFIX}{current_idx}")
                    if is_unhealthy:
                        logger.debug(f"[KeyRotator] Key index {current_idx} is unhealthy, skipping.")
                        continue
                except Exception as e:
                    logger.debug(f"[KeyRotator] Redis unhealthy check failed for index {current_idx}: {e}")

            # Found a healthy key, mark it as current
            self.index = current_idx

            # If session-based, update sticky mapping in Redis
            if session_id and self._use_redis:
                try:
                    await self.client.set(f"{self.STICKY_PREFIX}{session_id}", current_idx, ex=3600)
                except Exception as e:
                    logger.debug(f"[KeyRotator] Redis sticky set failed for session {session_id}: {e}")

            return key

        # Fallback: All unhealthy?
        # R106.1: If everything is dead, don't just return index 0.
        # Check if there's an index that is only on a 60s cooldown vs 24h.
        best_fallback = start_index % num_keys
        if self._use_redis:
            try:
                for i in range(num_keys):
                    idx = (start_index + i) % num_keys
                    reason = await self.client.get(f"{self.UNHEALTHY_PREFIX}{idx}")
                    if reason and "daily" not in reason.lower() and "quota" not in reason.lower():
                        # This key is only on a short RPM cooldown, better than a daily one
                        best_fallback = idx
                        break
            except Exception:
                pass

        logger.warning(f"[KeyRotator] All {num_keys} keys are unhealthy! Forcing best fallback key index {best_fallback}.")
        return self.keys[best_fallback]

    async def set_success(self, key: str, session_id: Optional[str] = None):
        """Marks a key as successful."""
        try:
            idx = self.keys.index(key)
            self.index = idx
            if self._use_redis:
                await self.client.set(self.SUCCESS_INDEX_KEY, idx)
                await self.client.delete(f"{self.UNHEALTHY_PREFIX}{idx}")
                if session_id:
                    await self.client.set(f"{self.STICKY_PREFIX}{session_id}", idx, ex=3600)
        except ValueError:
            logger.warning(f"[KeyRotator] set_success called with unknown key (not in pool).")
        except Exception as e:
            logger.warning(f"[KeyRotator] set_success Redis error: {e}")

    async def mark_unhealthy(self, key: str, reason: str = "rate_limit", session_id: Optional[str] = None):
        """Triggers circuit breaker cooldown: 60s RPM, 1h auth, 24h RPD."""
        try:
            idx = self.keys.index(key)
            reason_lower = reason.lower()

            if "daily" in reason_lower or "quota" in reason_lower:
                cooldown = self.COOLDOWN_DAILY
            elif "auth" in reason_lower or "invalid" in reason_lower or "server" in reason_lower:
                cooldown = self.COOLDOWN_AUTH
            else:
                cooldown = self.COOLDOWN_MINUTE

            if self._use_redis:
                await self.client.set(f"{self.UNHEALTHY_PREFIX}{idx}", reason, ex=cooldown)
                logger.warning(f"[KeyRotator] Key index {idx} UNHEALTHY. Reason: {reason}. Cooldown: {cooldown}s")
        except ValueError:
            logger.warning(f"[KeyRotator] mark_unhealthy called with unknown key (not in pool).")
        except Exception as e:
            logger.warning(f"[KeyRotator] mark_unhealthy Redis error: {e}")

    def get_count(self) -> int:
        return len(self.keys)

    def get_all_keys(self) -> list[str]:
        """Legacy support for multi-key iteration (V60.0)"""
        return self.keys

    def get_next_key(self) -> str:
        """Simple round-robin without unhealthy check (V56.0 compat)"""
        if not self.keys: return ""
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key


# Module-level singleton
key_rotator = SmartKeyRotator()
