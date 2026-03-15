import os
import logging
import time
import random
import hashlib
import asyncio
import redis.asyncio as redis
from typing import Optional, List, Dict

logger = logging.getLogger("api-gateway")

class SmartKeyRotator:
    """
    R101/R106: Intelligent Key Management for LLM Tiers.
    V70.0: Weighted Random Selection, Exponential Backoff, and TPM Tracking.
    """
    SUCCESS_INDEX_KEY = "ai:key_rotator:last_success_index"
    ROUND_ROBIN_KEY = "ai:key_rotator:round_robin_counter"
    STICKY_PREFIX = "ai:key_rotator:sticky:"
    
    # New V70.0 Redis Keys
    METADATA_PREFIX = "ai:key:v70:meta:"     # Hash: fail_count, last_used, health_score
    TPM_PREFIX = "ai:key:v70:tpm:"           # ZSET for sliding window token tracking
    BLACKLIST_PREFIX = "ai:key:v70:black:"   # Set/Key for dead keys (auth fail, etc)
    MODEL_DAILY_PREFIX = "ai:key:v70:daily:" # Key for (key, model) daily quota exhaustion
    POISON_PREFIX = "ai:model:v75:poison:"   # Model-wide blacklist (404, deprecated)
    DISCOVERED_MODELS_KEY = "ai:bridge:discovered:v75"

    # Cooldown settings
    BASE_COOLDOWN = 60
    MAX_COOLDOWN = 86400  # 24h
    
    # Google API Safety Limits (Mức an toàn free tier, chống 429)
    # Free Tier Pro (gemini-2.5-pro, gemini-3.x-pro): limit thực tế là 2 RPM!
    # Free Tier Flash (gemini-2.x-flash): limit là 10 RPM.
    # Paid Tier: có thể set cao hơn qua GEMINI_MAX_RPM trong .env
    MAX_RPM = int(os.getenv("GEMINI_MAX_RPM", 2))        # Default an toàn nhất cho Free Tier Pro
    MAX_TPM = int(os.getenv("GEMINI_MAX_TPM", 800000))   # Limit là 1M, set 800k an toàn dư dả
    
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
        
        self.keys = []
        self.index = 0
        self._use_redis = False
        self.client: Optional[redis.Redis] = None

        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self._use_redis = True
            logger.info(f"[KeyRotator] V70.0 Connected to Redis.")
        except Exception as e:
            logger.warning(f"[KeyRotator] Redis unavailable: {e}")

    async def load_keys(self):
        """Standardized Key Loading: Merges ENV and DB keys (V72.0)."""
        # 1. From Environment
        raw_env_keys = os.getenv("GEMINI_API_KEY", "")
        env_keys = [k.strip() for k in raw_env_keys.split(",") if k.strip()]
        
        # 2. From Database (Rule R102)
        db_keys = []
        try:
            db_keys = await self._recover_from_db()
        except Exception as e:
            logger.warning(f"[KeyRotator] Could not recover keys from DB: {e}")

        # 3. Merge & Deduplicate
        all_keys = list(dict.fromkeys(env_keys + db_keys))
        self.keys = all_keys
        self.index = 0
        
        if self._use_redis:
            logger.info(f"[KeyRotator] Pool refreshed. Total unique keys: {len(self.keys)} (ENV: {len(env_keys)}, DB: {len(db_keys)})")
        
        if not self.keys:
            logger.warning("[KeyRotator] NO Gemini keys found in ENV or DB!")

    async def _recover_from_db(self) -> list[str]:
        """Recovers Gemini keys from the primary VoiceProfile in the database."""
        from backend.database.alchemy_config import alchemy_config
        from backend.database.models import VoiceProfile
        from backend.utils.security import GeminiSecurity
        from sqlalchemy import select

        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            # We take the first active profile or iterate all
            stmt = select(VoiceProfile).where(VoiceProfile.gemini_keys_enc != None)
            result = await session.execute(stmt)
            profiles = result.scalars().all()
            
            recovered = []
            for p in profiles:
                keys = GeminiSecurity.decrypt_keys(p.gemini_keys_enc)
                recovered.extend(keys)
            
            return list(set(recovered)) # Unique

    def _get_key_id(self, key: str) -> str:
        """Standardize key identification via SHA256 (Truncated) for 2026 standards."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    async def get_key(self, session_id: Optional[str] = None) -> str:
        """
        V70.1: Weighted Random Selection with Key-Hash based tracking.
        """
        if not self.keys: return ""
        if not self._use_redis: return self.get_next_key()

        num_keys = len(self.keys)
        candidate_indices = []
        weights = []
        now = time.time()

        # R1.2 Gather health data for all candidate keys
        for idx, key in enumerate(self.keys):
            kid = self._get_key_id(key)
            
            # 1. Check Blacklist
            if await self.client.exists(f"{self.BLACKLIST_PREFIX}{kid}"):
                continue

            # 2. Check Cooldown/Health
            meta = await self.client.hgetall(f"{self.METADATA_PREFIX}{kid}")
            fail_count = int(meta.get("fail_count", 0))
            last_used = float(meta.get("last_used", 0))
            health_score = int(meta.get("health_score", 100))

            if fail_count > 0:
                cooldown = min(self.BASE_COOLDOWN * (2 ** (fail_count - 1)), self.MAX_COOLDOWN)
                if now - last_used < cooldown:
                    continue 

            # 3. Chủ động kiểm tra Limits (RPM & TPM) trước khi chọn key
            try:
                # Cleanup records cũ
                await self.client.zremrangebyscore(f"{self.TPM_PREFIX}{kid}", 0, now - 60)
                tpm_members = await self.client.zrangebyscore(f"{self.TPM_PREFIX}{kid}", now - 60, now)
                
                current_rpm = len(tpm_members)
                current_tpm = sum(int(m.split(":")[1]) for m in tpm_members if ":" in m and len(m.split(":")) >= 2)
                
                if current_rpm >= self.MAX_RPM or current_tpm >= self.MAX_TPM:
                    continue  # Bỏ qua key này nếu đang bị nóng, để Google không khóa
            except Exception as e:
                logger.debug(f"[KeyRotator] Bỏ qua lỗi check TPM cho {kid}: {e}")

            # 4. Calculate Weight
            idle_time = now - last_used
            weight = (idle_time + 1) * (health_score / 100.0)
            
            candidate_indices.append(idx)
            weights.append(weight)

        if not candidate_indices:
            logger.warning("[KeyRotator] TẤT CẢ API KEY đều quá tải (vượt Limit/Cooldown). Chặn request để bảo vệ tài khoản.")
            raise Exception("429 Too Many Requests: Hệ thống AI đang tạm thời đạt giới hạn an toàn. Vui lòng đợi 1 phút để hồi phục.")

        # 5. Weighted Random Choice
        chosen_idx = random.choices(candidate_indices, weights=weights, k=1)[0]
        chosen_key = self.keys[chosen_idx]
        chosen_kid = self._get_key_id(chosen_key)
        
        # 6. Lock-in tức thì để chống Race-Condition (dùng chung key do chưa kíp nhảy sleep)
        await self.client.hset(f"{self.METADATA_PREFIX}{chosen_kid}", "last_used", now)
        self.index = chosen_idx
        
        # 7. Micro-Jitter (Standard Anti-Scraping) nhảy sau khi đã lock key
        await asyncio.sleep(random.uniform(0.05, 0.15))
        
        return chosen_key

    async def mark_model_daily(self, key: str, model_name: str):
        """Mark (key, model) pair as daily-quota-exhausted. Auto-expires in 24h."""
        if not self._use_redis or not self.client: return
        kid = self._get_key_id(key)
        # Use model slug to avoid Redis key issues
        model_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        redis_key = f"{self.MODEL_DAILY_PREFIX}{kid}:{model_slug}"
        try:
            await self.client.set(redis_key, "DAILY_EXHAUSTED", ex=self.MAX_COOLDOWN)  # 24h TTL
            logger.warning(f"[KeyRotator] Key {kid[:8]} daily quota exhausted for model '{model_name}'. Auto-recovers in 24h.")
        except Exception as e:
            logger.error(f"[KeyRotator] Failed to mark model daily quota: {e}")

    async def is_model_daily_exhausted(self, key: str, model_name: str) -> bool:
        """Check if (key, model) daily quota is exhausted."""
        if not self._use_redis or not self.client: return False
        kid = self._get_key_id(key)
        model_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        redis_key = f"{self.MODEL_DAILY_PREFIX}{kid}:{model_slug}"
        try:
            return bool(await self.client.exists(redis_key))
        except Exception:
            return False

    async def mark_model_poisoned(self, model_name: str, reason: str = "404"):
        """Mark a model as poisoned (globally unhealthy/non-existent) for 24h."""
        if not self._use_redis or not self.client: return
        model_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        redis_key = f"{self.POISON_PREFIX}{model_slug}"
        try:
            await self.client.set(redis_key, reason, ex=self.MAX_COOLDOWN)
            logger.warning(f"[KeyRotator] Model '{model_name}' POISONED. Blacklisted for 24h. Reason: {reason}")
        except Exception:
            pass

    async def is_model_poisoned(self, model_name: str) -> bool:
        """Check if a model is globally poisoned."""
        if not self._use_redis or not self.client: return False
        model_slug = model_name.replace("/", "_").replace("-", "_")[:40]
        redis_key = f"{self.POISON_PREFIX}{model_slug}"
        try:
            return bool(await self.client.exists(redis_key))
        except Exception:
            return False

    async def save_discovered_models(self, models: list[str]):
        """Save the list of discovered models to Redis."""
        if not self._use_redis or not self.client: return
        try:
            import json
            await self.client.set(self.DISCOVERED_MODELS_KEY, json.dumps(models), ex=self.MAX_COOLDOWN)
            logger.info(f"[KeyRotator] Saved {len(models)} discovered models to Redis.")
        except Exception:
            pass

    async def get_discovered_models(self) -> list[str]:
        """Get the cached list of discovered models."""
        if not self._use_redis or not self.client: return []
        try:
            import json
            val = await self.client.get(self.DISCOVERED_MODELS_KEY)
            return json.loads(val) if val else []
        except Exception:
            return []

    async def set_success(self, key: str, session_id: Optional[str] = None):
        """Marks a key as successful, resets fail_count using Hash ID."""
        if not self._use_redis: return
        kid = self._get_key_id(key)
        try:
            await self.client.hset(f"{self.METADATA_PREFIX}{kid}", mapping={
                "fail_count": 0,
                "health_score": 100
            })
        except Exception:
            pass

    async def mark_unhealthy(self, key: str, reason: str = "rate_limit", session_id: Optional[str] = None):
        """Circuit Breaker Logic using Hash ID."""
        if not self._use_redis: return
        kid = self._get_key_id(key)
        reason_lower = reason.lower()
        now = time.time()
        
        # 1. Critical Failures -> Blacklist (Khoá vĩnh viễn trong phiên)
        if any(p in reason_lower for p in ["auth", "invalid", "disabled", "expired", "401", "403"]):
            await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", reason, ex=self.MAX_COOLDOWN * 30)
            logger.error(f"[KeyRotator] Key {kid[:8]} (hash) BLACKLISTED. Reason: {reason}")
            return

        # 2. Daily Quota Exceeded -> Semi-Blacklist (Khóa 24h)
        if "daily" in reason_lower or "quota" in reason_lower:
             await self.client.set(f"{self.BLACKLIST_PREFIX}{kid}", f"DAILY_LIMIT_REACHED: {reason}", ex=self.MAX_COOLDOWN)
             logger.warning(f"[KeyRotator] Key {kid[:8]} hit DAILY QUOTA. Locked for 24h.")
             return

        # 3. Soft 429 (Transient Rate Limit) -> No fail_count increment
        # Thay vào đó, ta đánh dấu key này đang "bận" bằng cách nạp ảo vào TPM sliding window
        # Điều này giúp key được nghỉ ngơi 1 phút mà không bị nâng fail_count lên cao (tránh cooldown 2, 4, 8h...)
        if reason_lower == "rate_limit" or "429" in reason_lower:
            logger.warning(f"[KeyRotator] Key {kid[:8]} hit soft rate_limit. Resting temporarily.")
            # Nạp ảo 1 request vào TPM để current_rpm tăng lên, loop skip key này tự nhiên
            await self.track_tokens(key, 100) # Thêm ảo 100 tokens để "lấp" quota
            await self.client.hset(f"{self.METADATA_PREFIX}{kid}", "last_used", now)
            return

        # 4. Other Transient Failures -> Exponential Backoff
        fail_count = await self.client.hincrby(f"{self.METADATA_PREFIX}{kid}", "fail_count", 1)
        await self.client.hset(f"{self.METADATA_PREFIX}{kid}", mapping={
            "health_score": max(0, 100 - (fail_count * 20)),
            "last_used": now
        })
        logger.warning(f"[KeyRotator] Key {kid[:8]} (hash) fail_count={fail_count}. Reason: {reason}")

    async def track_tokens(self, key: str, tokens: int):
        """Track tokens for TPM/RPM management using Hash ID sliding window."""
        if not self._use_redis or tokens <= 0: return
        kid = self._get_key_id(key)
        now = time.time()
        # Format: timestamp:tokens:random_id (để zadd không đè member trùng thời gian)
        member = f"{now}:{tokens}:{random.randint(10000, 99999)}"
        try:
            async with self.client.pipeline() as pipe:
                pipe.zadd(f"{self.TPM_PREFIX}{kid}", {member: now})
                pipe.zremrangebyscore(f"{self.TPM_PREFIX}{kid}", 0, now - 60)
                await pipe.execute()
        except Exception as e:
            logger.warning(f"[KeyRotator] Tracking token lỗi tạm thời: {e}")

    async def reset_health(self) -> int:
        """Clears ALL health metadata and blacklists from Redis (Rule R101)."""
        if not self._use_redis or not self.client:
            return 0
        
        cleared = 0
        try:
            # 1. Clear Blacklists
            async for k in self.client.scan_iter(f"{self.BLACKLIST_PREFIX}*"):
                await self.client.delete(k)
                cleared += 1
            
            # 2. Reset Metadata
            async for k in self.client.scan_iter(f"{self.METADATA_PREFIX}*"):
                await self.client.hset(k, mapping={"fail_count": 0, "health_score": 100})
                cleared += 1
            
            # 3. Clear MODEL-LEVEL daily exhaustion
            async for k in self.client.scan_iter(f"{self.MODEL_DAILY_PREFIX}*"):
                await self.client.delete(k)
                cleared += 1

            # 4. Clear TPM windows (Force full fresh start)
            async for k in self.client.scan_iter(f"{self.TPM_PREFIX}*"):
                await self.client.delete(k)
                cleared += 1

            # 4. Reload from DB/ENV
            await self.load_keys()
            
            return cleared
        except Exception as e:
            logger.error(f"[KeyRotator] Reset failed: {e}")
            return cleared

    def get_count(self) -> int:
        return len(self.keys)

    def get_next_key(self) -> str:
        if not self.keys: return ""
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

# Module-level singleton
key_rotator = SmartKeyRotator()
