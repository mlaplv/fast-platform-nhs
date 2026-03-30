import hashlib
import logging
import os
import time
import re
import unicodedata
from typing import Optional, Dict, Tuple
import redis.asyncio as _redis

logger = logging.getLogger("api-gateway")

class AntiSpamService:
    """
    R23: Real-time Anti-Spam Shield (V56.6 - FORTRESS MODE).
    Optimized for High-Volume Ad Campaigns with Atomic Lua Scripts & Smart Weighting.
    """
    def __init__(self, redis_client: Optional[_redis.Redis] = None):
        self.redis = redis_client
        # Fortress Mode Thresholds
        self.PRO_THRESHOLD_SCORE = 90.0
        self.AUDIT_THRESHOLD_SCORE = 70.0
        self.MAX_ORDERS_24H = 3
        self.RAPID_FIRE_SECONDS = 5
        self.BLACKLIST_DURATION = 86400  # 24h
        
        # LUA Script: Atomic Velocity Tracking & Rapid Fire Prevention
        # Guarantees thread-safe execution against parallel Botnet attacks
        self.LUA_VELOCITY_SCRIPT = """
            local key = KEYS[1]
            local last_key = KEYS[2]
            local duration = tonumber(ARGV[1])
            local now = tonumber(ARGV[2])
            
            -- Track volume
            local count = redis.call('incr', key)
            if count == 1 then
                redis.call('expire', key, duration)
            end
            
            -- Get last timestamp
            local last_ts = redis.call('get', last_key)
            
            -- Update last timestamp
            redis.call('setex', last_key, 60, tostring(now))
            
            return {count, last_ts}
        """

    def generate_fingerprint(self, ip: str, user_agent: str, extra: str = "") -> str:
        raw = f"{ip}|{user_agent}|{extra}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def normalize_address(self, address: str) -> str:
        if not address: return ""
        addr = address.lower().strip()
        addr = re.sub(r'\s+', ' ', addr)
        addr = "".join(c for c in unicodedata.normalize('NFD', addr) if unicodedata.category(c) != 'Mn')
        addr = addr.replace('đ', 'd').replace('Đ', 'd')
        return addr

    async def check_order_spam(
        self,
        ip: str,
        user_agent: str,
        tenant_id: str,
        order_data: dict,
        is_campaign_mode: bool = False
    ) -> Tuple[bool, str, float, str]:
        """
        Fortress Mode: Weighed Multi-Vector Defense
        is_campaign_mode=True: Relaxes quantity checks, tightens identity rotation checks.
        """
        fingerprint = self.generate_fingerprint(ip, user_agent)
        phone = order_data.get("phone", "unspecified")

        # R2026: Dev-Mode Bypass — tránh false positive khi test/seed trong môi trường development
        if os.getenv("ENVIRONMENT", "production") == "development":
            logger.debug(f"[AntiSpam] DEV MODE BYPASS for order (phone={phone})")
            return False, "Dev Mode Bypass", 0.0, fingerprint

        if not self.redis:
            return False, "Bypass: Redis Off", 0.0, fingerprint

        # R2026: Elite V2.2: Developer/Sếp Whitelist Bypass
        # Check if phone is in whitelist to prevent false positives during testing
        if phone != "unspecified":
            is_whitelisted = await self.redis.sismember("spam:whitelist:phones", phone)
            if is_whitelisted:
                logger.info(f"[AntiSpam] Whitelist Bypass for phone: {phone}")
                return False, "Whitelist Bypass", 0.0, fingerprint
        address = self.normalize_address(order_data.get("address", ""))
        addr_hash = hashlib.sha256(address.encode()).hexdigest() if address else "no_addr"
        
        score = 0.0
        reasons = []
        now = int(time.time())

        # Sub-routine: Evaluate PII completeness (Prevent silent bypasses)
        if phone == "unspecified" or not phone.strip():
            score += 40.0
            reasons.append("Incomplete PII (Missing Phone)")
        
        # Sub-routine: Vector Tracking with Atomic Lua (24h Window)
        vectors = [
            ("fp", fingerprint),
            ("phone", phone),
            ("addr", addr_hash)
        ]

        for v_type, v_val in vectors:
            if v_val == "unspecified" or v_val == "no_addr": continue
            
            key = f"spam:v2026:{v_type}:{v_val}"
            last_key = f"spam:last:{v_type}:{v_val}"
            
            # ATOMIC Lua Execution
            try:
                res = await self.redis.eval(
                    self.LUA_VELOCITY_SCRIPT,
                    2, # num_keys
                    key,
                    last_key,
                    self.BLACKLIST_DURATION,
                    now
                )
                count = int(res[0])
                last_ts = res[1]
                
                # Volume Logic
                if count > self.MAX_ORDERS_24H:
                    score += 60.0
                    reasons.append(f"Professional Cluster Detect ({v_type.upper()}:{count})")
                
                # Rapid Fire Logic
                if last_ts and (now - int(last_ts)) < self.RAPID_FIRE_SECONDS:
                    score += 50.0 # High penalty for Rapid Fire
                    reasons.append(f"Rapid Fire Burst ({v_type.upper()})")
                    
            except Exception as e:
                logger.error(f"[AntiSpam] Lua Script Error: {e}")

        # Sub-routine: Cross-vector Correlation (Identity Rotation vs Office/Dorm False Positives)
        phone_cluster_key = f"spam:sync:phone:{phone}"
        addr_cluster_key = f"spam:sync:addr:{addr_hash}"
        
        if phone != "unspecified" and addr_hash != "no_addr":
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.sadd(phone_cluster_key, fingerprint)
                pipe.expire(phone_cluster_key, self.BLACKLIST_DURATION)
                pipe.scard(phone_cluster_key)
                
                pipe.sadd(addr_cluster_key, phone)
                pipe.expire(addr_cluster_key, self.BLACKLIST_DURATION)
                pipe.scard(addr_cluster_key)
                
                res = await pipe.execute()
                fp_count = res[2]
                addr_phones_count = res[5]
                
                # Clone Farm: 1 Phone shared across many device fingerprints
                if fp_count > 1:
                    penalty = 80.0 if is_campaign_mode else 50.0  # Stricter in Campaign Mode
                    score += penalty
                    reasons.append(f"Identity Rotation (Phone used by {fp_count} dev fingerprints)")
                
                # Office/Dorm False Positive Mitigation
                # If same address has many phones, but FP count per phone is 1 -> Valid Cluster
                if addr_phones_count > 2 and fp_count == 1:
                    score -= 30.0  # Trust bonus
                    score = max(0.0, score) # Floor at 0
                    reasons.append("Office/Dorm Cluster Detected (Trust +)")

        # Sub-routine: Heuristics based on Mode
        items = order_data.get("items", [])
        if not is_campaign_mode:
            # Standard Strict Mode
            if len(items) > 10:
                score += 30.0
                reasons.append("Bulk Order Anomaly")
            for item in items:
                if item.get("quantity", 0) > 20:
                    score += 50.0
                    reasons.append("Stock Drain Attempt")
        else:
            # Campaign Mode: Loose Quantity check, assuming Flash Sale
            pass

        # Result Evaluation
        is_spam = score >= self.PRO_THRESHOLD_SCORE
        final_reason = " | ".join(reasons) if reasons else "Legitimate"
        
        if score >= self.AUDIT_THRESHOLD_SCORE and not is_spam:
            final_reason = f"PENDING_AUDIT: {final_reason}"
            is_spam = True 

        return is_spam, final_reason, min(score, 100.0), fingerprint

# apps/api-gateway/src/services/anti_spam.py
from backend.services.xohi_memory import xohi_memory
anti_spam_service = AntiSpamService(redis_client=xohi_memory.client)
