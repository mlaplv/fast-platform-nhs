import hashlib
import logging
import os
import time
import re
import unicodedata
from typing import Optional, Dict, Tuple, List, Union, TypedDict, cast # type: ignore
import redis.asyncio as _redis # type: ignore
from pydantic_ai import Agent # type: ignore
from pydantic import BaseModel, Field
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge # type: ignore
from backend.services.xohi.prompts import composer

logger = logging.getLogger("api-gateway")

class OrderItemSpamData(TypedDict):
    id: str
    quantity: int

class OrderSpamData(TypedDict, total=False):
    phone: str
    name: str
    address: str
    total: float
    items: List[OrderItemSpamData]

class AntiSpamService:
    def __init__(self, redis_client: Optional[_redis.Redis] = None):
        self.redis = redis_client
        self.client = redis_client
        import asyncio
        self._background_tasks: set[asyncio.Task[object]] = set()
        
        self.BLOCK_THRESHOLD_SCORE = 90.0      # Tier 3: Block — từ chối ngay
        self.CHALLENGE_THRESHOLD_SCORE = 70.0   # Tier 2: Challenge — yêu cầu xác nhận thêm
        self.AUDIT_THRESHOLD_SCORE = 50.0       # Tier 1: Audit — lưu & gắn cờ để review
        # Legacy alias cho backward compat
        self.PRO_THRESHOLD_SCORE = self.BLOCK_THRESHOLD_SCORE
        self.MAX_ORDERS_24H = 3
        self.RAPID_FIRE_SECONDS = 5
        self.BLACKLIST_DURATION = 86400
        
        # Viral 2026: Troll Keywords (VN Context)
        self.TROLL_KEYWORDS: List[str] = [
            "test", "abc", "asdf", "qwer", "zxcv",
            "cho", "mẹ mày", "me may", "lua dao", "lừa đảo",
            "bố mày", "bo may", "concac", "clmm", "dmm"
        ]
        
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


    def generate_device_hash(self, ip: str, user_agent: str, extra: str = "") -> str:
        raw = f"{ip}|{user_agent}|{extra}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def normalize_address(self, address: str) -> str:
        if not address: return ""
        addr = address.lower().strip()
        addr = re.sub(r'\s+', ' ', addr)
        addr = "".join(c for c in unicodedata.normalize('NFD', addr) if unicodedata.category(c) != 'Mn')
        addr = addr.replace('đ', 'd').replace('Đ', 'd')
        return addr

    def is_valid_vn_phone(self, phone: str) -> bool:
        """Viral 2026: Strict VN Phone Validator."""
        clean_phone: str = re.sub(r'[^0-9]', '', phone)
        # Convert +84 or 84 prefix to 0
        clean_phone = re.sub(r'^84', '0', clean_phone)
        return bool(re.match(r'^0(3|5|7|8|9)[0-9]{8}$', clean_phone))

    def has_troll_content(self, *texts: str) -> bool:
        """Viral 2026: Detect competitor/spam keyboard mashing or insults."""
        for text in texts:
            if not text: continue
            norm_text = self.normalize_address(text)
            if any(kw in norm_text for kw in self.TROLL_KEYWORDS):
                return True
        return False

    async def agentic_address_review(self, name: str, address: str) -> float:
        """Viral 2026: Agentic NLP Analysis for Address & Name via TrinityBridge."""
        try:
            if len(address) < 5: return 50.0 
            
            # 1. Dynamic Agent via TrinityBridge (Elite V2.2 Unity)
            agent = Agent(
                system_prompt=composer.compose("antispam_fraud_premium")
            )

            # Utilize the centralized bridge for military-grade stability
            result = await trinity_bridge.run(
                agent=agent,
                prompt=f"Name: {name}, Address: {address}",
                role="fast",
                timeout=30.0
            )

            if result:
                raw_score = str(getattr(result, "data", getattr(result, "output", result))).strip()
                match = re.search(r"(\d+\.?\d*)", raw_score)
                return float(match.group(1)) if match else 0.0
            
            return 0.0
        except Exception as e:
            logger.error(f"[AntiSpam] Fatal Agentic Error: {e}")
            return 0.0 

    async def _background_ai_flag(self, name: str, address: str, current_score: float, reasons: List[str]) -> None:
        """
        [P-01] Fire-and-Forget: Chạy AI review trong background task.
        Không block checkout. Log kết quả để admin review.
        """
        try:
            ai_penalty = await self.agentic_address_review(name, address)
            if ai_penalty > 50.0:
                final = min(current_score + ai_penalty, 100.0)
                logger.warning(
                    f"[AntiSpam-BG] AI review complete: score {current_score:.1f} → {final:.1f} "
                    f"(AI penalty={ai_penalty:.1f}) | name='{name}' addr='{address[:40]}'"
                )
            else:
                logger.debug(f"[AntiSpam-BG] AI review: Legitimate (penalty={ai_penalty:.1f})")
        except Exception as e:
            logger.error(f"[AntiSpam-BG] Background AI review error: {e}")

    async def check_order_spam(
        self,
        ip: str,
        user_agent: str,
        tenant_id: str,
        order_data: OrderSpamData,
        is_campaign_mode: bool = False
    ) -> Tuple[bool, str, float, str]:
        device_hash: str = self.generate_device_hash(ip, user_agent)
        phone_val = order_data.get("phone", "unspecified")
        phone: str = str(phone_val) if phone_val else "unspecified"

        if os.getenv("ENVIRONMENT", "production").lower().strip() == "development" \
                and os.getenv("ALLOW_SPAM_BYPASS", "false").lower().strip() == "true":
            logger.warning("[AntiSpam] ⚠️ DEV SPAM BYPASS ACTIVE — NEVER ENABLE IN PRODUCTION!")
            return False, "Dev Mode Bypass", 0.0, device_hash

        if not self.redis:
            return False, "Bypass: Redis Off", 0.0, device_hash

        if phone != "unspecified" and self.redis is not None:
            redis_inst = cast(_redis.Redis, self.redis)
            # 1. VIP Customer Recognition (Direct Pass)
            if await redis_inst.sismember("spam:vip:phones", phone):
                logger.info(f"[AntiSpam] VIP Pass for phone: {phone}")
                return False, "VIP Customer Trust", 0.0, device_hash

            # 2. Whitelist Bypass
            if await redis_inst.sismember("spam:whitelist:phones", phone):
                logger.info(f"[AntiSpam] Whitelist Bypass for phone: {phone}")
                return False, "Whitelist Bypass", 0.0, device_hash
        
        # 3. Viral 2026: Identity & Content Validation
        address_val = order_data.get("address", "")
        address = self.normalize_address(str(address_val))
        addr_hash = hashlib.sha256(address.encode()).hexdigest() if address else "no_addr"
        
        score: float = 0.0
        reasons: List[str] = []
        now = int(time.time())

        name = str(order_data.get("name", ""))
        raw_phone = str(order_data.get("phone", ""))
        
        if self.has_troll_content(name, address):
            return True, "Competitor Troll Detected", 100.0, device_hash
            
        if not self.is_valid_vn_phone(raw_phone):
            score += 80.0
            reasons.append("Invalid Vietnam Phone Format")

        # Sub-routine: Evaluate PII completeness
        if phone == "unspecified" or not phone.strip():
            score += 40.0
            reasons.append("Incomplete PII (Missing Phone)")
        
        # Sub-routine: Vector Tracking with Atomic Lua (24h Window)
        vectors = [
            ("fp", device_hash),
            ("phone", phone),
            ("addr", addr_hash)
        ]

        for v_type, v_val in vectors:
            if v_val == "unspecified" or v_val == "no_addr": continue
            
            key: str = f"spam:v2026:{v_type}:{v_val}"
            last_key: str = f"spam:last:{v_type}:{v_val}"
            
            # ATOMIC Lua Execution
            if self.redis is not None:
                redis_inst = cast(_redis.Redis, self.redis)
                try:
                    res_raw = await redis_inst.eval(
                        self.LUA_VELOCITY_SCRIPT,
                        2, # num_keys
                        key,
                        last_key,
                        self.BLACKLIST_DURATION,
                        now
                    )
                    # Force cast to list for indexing
                    res_list: List[Union[str, int, float, None]] = list(res_raw) if isinstance(res_raw, (list, tuple)) else []
                    
                    count: int = int(res_list[0]) if len(res_list) > 0 and res_list[0] is not None else 0
                    last_ts_val = res_list[1] if len(res_list) > 1 else None
                    
                    # Volume Logic
                    if count > self.MAX_ORDERS_24H:
                        score = cast(float, score) + 60.0
                        reasons.append(f"Professional Cluster Detect ({v_type.upper()}:{count})")
                    
                    # Rapid Fire Logic
                    if last_ts_val is not None:
                        ts_int: int = int(str(last_ts_val))
                        if (now - ts_int) < self.RAPID_FIRE_SECONDS:
                            score = cast(float, score) + 50.0
                            reasons.append(f"Rapid Fire Burst ({v_type.upper()})")
                except Exception as e:
                    logger.error(f"[AntiSpam] Lua Script Error: {e}")

        phone_cluster_key = f"spam:sync:phone:{phone}"
        addr_cluster_key = f"spam:sync:addr:{addr_hash}"

        if phone != "unspecified" and addr_hash != "no_addr" and self.redis is not None:
            redis_inst = cast(_redis.Redis, self.redis)
            async with redis_inst.pipeline(transaction=True) as pipe:
                pipe.sadd(phone_cluster_key, device_hash)
                pipe.expire(phone_cluster_key, self.BLACKLIST_DURATION)
                pipe.scard(phone_cluster_key)
                
                pipe.sadd(addr_cluster_key, phone)
                pipe.expire(addr_cluster_key, self.BLACKLIST_DURATION)
                pipe.scard(addr_cluster_key)
                
                # Redis execute returns a list of results from the pipeline (int/bool)
                res_raw_pipe = await pipe.execute()
                res_pipe: List[int] = [int(v) if isinstance(v, (int, bool)) else 0 for v in res_raw_pipe]
                
                fp_count: int = res_pipe[2] if len(res_pipe) > 2 else 0
                addr_phones_count: int = res_pipe[5] if len(res_pipe) > 5 else 0
                
                if fp_count > 1:
                    score = cast(float, score) + (80.0 if is_campaign_mode else 50.0)
                    reasons.append(f"Identity Rotation (Phone used by {fp_count} dev hashes)")
                
                if addr_phones_count > 2 and fp_count == 1:
                    score -= 30.0
                    score = 0.0 if score < 0.0 else score
                    reasons.append("Office/Dorm Cluster Detected (Trust +)")

        items_val = order_data.get("items", [])
        items = list(items_val) if isinstance(items_val, list) else []
        
        if not is_campaign_mode:
            if len(items) > 10:
                score += 30.0
                reasons.append("Bulk Order Anomaly")
            for item in items:
                qty_val = item.get("quantity", 0)
                if int(qty_val) > 20:
                    score = cast(float, score) + 50.0
                    reasons.append("Stock Drain Attempt")

        # Result Evaluation
        # 4. Viral 2026: Final Agentic Review — Fire-and-Forget để không block checkout <200ms
        # [P-01] AI review chạy background, không await trực tiếp trong hot path
        if self.CHALLENGE_THRESHOLD_SCORE > score >= 40.0:
            import asyncio
            task = asyncio.create_task(
                self._background_ai_flag(name, address, score, reasons)
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            logger.debug(f"[AntiSpam] Background AI review dispatched for score={score:.1f}")

        # [H-05] 3-Tier Response:
        # Tier 3 (>= 90): Block — từ chối ngay lập tức
        # Tier 2 (70-89): Challenge — mark spam để controller xử lý (CAPTCHA/OTP)
        # Tier 1 (50-69): Audit — lưu đơn nhưng gắn cờ PENDING_AUDIT
        # Tier 0 (< 50):  Legitimate — pass qua bình thường
        final_score = min(score, 100.0)
        final_reason = " | ".join(reasons) if reasons else "Legitimate"

        if final_score >= self.BLOCK_THRESHOLD_SCORE:
            is_spam = True
            final_reason = f"BLOCK: {final_reason}"
        elif final_score >= self.CHALLENGE_THRESHOLD_SCORE:
            is_spam = True  # Controller xử lý challenge, không nhất thiết phải reject cứng
            final_reason = f"CHALLENGE: {final_reason}"
        elif final_score >= self.AUDIT_THRESHOLD_SCORE:
            is_spam = False  # [H-05 Fix] Không block, chỉ audit — giảm false positive rate
            final_reason = f"PENDING_AUDIT: {final_reason}"
        else:
            is_spam = False

        return is_spam, final_reason, final_score, device_hash

# apps/api-gateway/src/services/anti_spam.py
from backend.services.xohi_memory import xohi_memory # type: ignore
anti_spam_service = AntiSpamService(redis_client=xohi_memory.client)
