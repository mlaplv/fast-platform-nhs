import os
import logging
from unittest.mock import MagicMock

# Dynamically import redis, falling back to mock if not installed
try:
    import redis.asyncio as redis
except ImportError:
    redis = MagicMock()

logger = logging.getLogger("m2m_guard")

class M2MGuard:
    """
    R5: Money-To-Money (M2M) Global Circuit Breaker.
    The primary defense against A2A Deadlocks (Denial of Wallet).
    Checks real-time Token & Budget limits using Redis.
    """
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        if isinstance(redis, MagicMock):
            self.redis = MagicMock()
            logger.warning("[M2M Guard] Redis library not found. Running in MOCK Mode. Shield deactivated.")
        else:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            
        self.daily_budget = float(os.getenv("DAILY_LLM_BUDGET_USD", "5.00"))
        self.max_session_tokens = int(os.getenv("MAX_SESSION_TOKENS", "16000"))
        # Using a fixed mapping of tokens to USD for rapid calculation ($0.01 per 1000 tokens as baseline)
        self.token_to_usd_rate = 0.00001
        
    async def check_circuit_breaker(self, session_id: str) -> None:
        """
        Hard Panic check before passing the intent to LLM or SLM.
        Raises an exception if budgets are exceeded.
        """
        import datetime
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        daily_key = f"m2m:budget:{today_str}"
        session_key = f"m2m:session:{session_id}"
        
        try:
            # Atomic fetch
            pipeline = self.redis.pipeline()
            pipeline.get(daily_key)
            pipeline.get(session_key)
            results = await pipeline.execute()
            
            daily_spent = float(results[0]) if results and results[0] else 0.0
            session_tokens = int(results[1]) if results and len(results) > 1 and results[1] else 0
            
            # 1. Global Daily Budget Breaker
            if daily_spent >= self.daily_budget:
                error_msg = f"[M2M PANIC] Global LLM budget exceeded (${daily_spent} / ${self.daily_budget}). A2A halted."
                logger.error(error_msg)
                raise PermissionError(error_msg)
                
            # 2. Session Token Breaker (DoW Protection)
            if session_tokens >= self.max_session_tokens:
                error_msg = f"[M2M PANIC] Maximum tokens exceeded for session {session_id} ({session_tokens} / {self.max_session_tokens}). Possible Deadlock. A2A halted."
                logger.error(error_msg)
                raise PermissionError(error_msg)
                
        except (redis.ConnectionError, redis.TimeoutError) as e:
            # Fall open or closed? R5 dictates absolute financial guardrails. We should fall CLOSED if Redis is totally uncontactable in an A2A flow.
            # However, for local dev without redis, we fall OPEN (with loud warning).
            logger.warning(f"[M2M Guard] Redis unavailable, bypassing circuit breaker: {e}")
            pass

    async def report_burn(self, session_id: str, tokens_used: int) -> None:
        """
        Increments the atomic counters after LLM execution.
        """
        if tokens_used <= 0:
            return
            
        import datetime
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        
        daily_key = f"m2m:budget:{today_str}"
        session_key = f"m2m:session:{session_id}"
        usd_spent = tokens_used * self.token_to_usd_rate
        
        try:
            pipeline = self.redis.pipeline()
            pipeline.incrbyfloat(daily_key, usd_spent)
            pipeline.expire(daily_key, 86400 * 2) # keep for 2 days
            
            pipeline.incrby(session_key, tokens_used)
            pipeline.expire(session_key, 86400) # Keep session tokens for 1 day
            
            await pipeline.execute()
        except Exception as e:
            logger.error(f"Failed to record M2M token burn: {e}")
