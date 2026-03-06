import hashlib
import logging
import time
from typing import Optional, Dict, Tuple
import redis.asyncio as _redis

logger = logging.getLogger("api-gateway")

class AntiSpamService:
    """
    R23: Real-time Anti-Spam Shield (V56.5).
    Protects against competitor click/order fraud via Device Fingerprinting and Velocity Checks.
    """
    def __init__(self, redis_client: Optional[_redis.Redis] = None):
        self.redis = redis_client
        # Thresholds (configurable via ENV in future)
        self.MAX_ORDERS_PER_HOUR = 5
        self.MAX_ORDERS_PER_MINUTE = 2

    def generate_fingerprint(self, ip: str, user_agent: str, extra: str = "") -> str:
        """Create a device fingerprint hash."""
        raw = f"{ip}|{user_agent}|{extra}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def check_velocity(self, fingerprint: str, tenant_id: str) -> Tuple[bool, str]:
        """
        Check if the current device/fingerprint has exceeded limits for this tenant.
        """
        if not self.redis:
            return False, "Redis unavailable, skipping check"

        minute_key = f"spam:min:{tenant_id}:{fingerprint}"
        hour_key = f"spam:hour:{tenant_id}:{fingerprint}"

        try:
            # 1. Velocity: Minute Check
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.incr(minute_key)
                pipe.expire(minute_key, 60)
                res = await pipe.execute()
                min_count = res[0]

            if min_count > self.MAX_ORDERS_PER_MINUTE:
                return True, f"Velocity limit exceeded (Minute): {min_count} orders"

            # 2. Velocity: Hour Check
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.incr(hour_key)
                pipe.expire(hour_key, 3600)
                res = await pipe.execute()
                hour_count = res[0]

            if hour_count > self.MAX_ORDERS_PER_HOUR:
                return True, f"Velocity limit exceeded (Hour): {hour_count} orders"

            return False, ""

        except Exception as e:
            logger.error(f"[AntiSpam] Velocity check failed: {e}")
            return False, "Check error"

    async def check_order_spam(self, ip: str, user_agent: str, tenant_id: str, order_data: dict) -> Tuple[bool, str, float]:
        """
        Holistic Anti-Spam Check:
        1. Device Fingerprinting (R88)
        2. Velocity Check (R88.5)
        3. Simple Heuristics
        Returns (is_spam, reason, score)
        """
        fingerprint = self.generate_fingerprint(ip, user_agent)
        is_spammed, reason = await self.check_velocity(fingerprint, tenant_id)
        
        score = 0.0
        if is_spammed:
            score = 100.0
            return True, f"Anti-Spam Shield: {reason}", score
            
        # Optional: Add more checks here
        
        return False, "Legitimate", 0.0

# Initialize with fallback (handled in controllers via DI or manual init)
anti_spam_service = None # To be initialized in main or controller
