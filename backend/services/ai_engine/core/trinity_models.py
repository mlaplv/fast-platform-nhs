from __future__ import annotations
import logging
import httpx
import time
from typing import Optional, TYPE_CHECKING
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models import SystemSetting

if TYPE_CHECKING:
    from .key_rotator import KeyRotator

logger = logging.getLogger("api-gateway")

# Elite V2.2: Hard blacklist — models that NEVER enter the AI chain
# These are either non-functional (no tool/function calling) or unstable.
# R45: Lite-preview removed from blacklist to allow Viral 2026 models.
HARD_BLACKLIST = [
    "gemma", "experimental", "alpha", "learnlm", "preview", "latest", 
    "exp", "-001", "-002", 
    "flash-latest", "lite-latest", "gemini-1.5"
]

DEFAULT_AI_CONFIG = {
    "role_patterns": {
        "fast": ["flash", "8b", "lite"],
        "brain": ["pro", "ultra", "brain"]
    },
    "blacklist": ["-tts", "-embedding", "-aqa", "-image", "-vision", "deep-research", "robotics", "lyria", "banana", "lite-preview", "gemini-flash-latest", "gemini-flash-lite-latest", "-preview", "exp", "-latest", "-001", "-002"],
    "lockdown": ["early-access", "alpha", "customtools"],
    "penalties": {
        "experimental": 100,
        "preview": 20,
        "lite": 50,
        "8b": 30
    },
    "error_mapping": {
        "auth_hard": ["api key not valid", "invalid_key", "key_expired", "project disabled", "deleted"],
        "auth_soft": ["401", "403", "unauthorized", "forbidden", "permission_denied", "user_location_not_supported"],
        "rate_limit": ["429", "quota", "rate limit", "limit reached", "resource_exhausted", "503", "unavailable", "500", "reset by peer", "deadline_exceeded", "interactions api"],
        "fail_fast": ["context_length_exceeded", "too many tokens", "safety", "blocked", "invalid_argument", "400"],
        "model_not_found": ["model not found", "404"]
    }
}

class TrinityModels:
    """Helper for model discovery and chain building (V76)."""
    
    def __init__(self, rotator: 'KeyRotator', default_model: str, fallback_model: str) -> None:
        self.rotator: 'KeyRotator' = rotator
        self.default_model: str = default_model
        self.fallback_model: str = fallback_model
        self.ROLE_FAST: str = "fast"
        self.ROLE_BRAIN: str = "brain"
        self._config: dict = DEFAULT_AI_CONFIG
        self._last_config_load: float = 0
        self._config_ttl: int = 300 # 5 minutes cache

    async def _ensure_config(self) -> None:
        """Elite V2.2: Fetch data-driven config from DB with TTL cache."""
        now = time.time()
        if now - self._last_config_load < self._config_ttl:
            return
            
        try:
            async with alchemy_config.create_session_maker()() as session:
                setting = (await session.execute(
                    select(SystemSetting).where(SystemSetting.key == "ai_orchestration_config")
                )).scalar_one_or_none()
                if setting and setting.value:
                    self._config = setting.value
                    logger.debug("[TrinityModels] AI Orchestration Config reloaded from DB.")
                self._last_config_load = now
        except Exception as e:
            logger.warning(f"[TrinityModels] Failed to load config from DB: {e}. Using cache/defaults.")
            self._last_config_load = now - (self._config_ttl / 2) # Retry sooner on failure

    async def discover_available(self) -> list[str]:
        await self._ensure_config()
        cached = await self.rotator.get_discovered_models()
        if cached: return cached

        # Elite V2.2: Try to get a key for the default model first
        key: Optional[str] = None
        try:
            key = await self.rotator.get_key(model_name=self.default_model)
        except Exception as e:
            # Fallback: Get ANY healthy key just for discovery purposes
            logger.debug(f"[TrinityModels] Specific key discovery failed: {e}. Trying fallback model.")
            try:
                # Elite V2.2: Use 2.0 Flash for discovery as it has the widest quota
                key = await self.rotator.get_key(model_name="gemini-2.0-flash")
            except Exception as e_inner:
                logger.warning(f"[TrinityModels] Full key discovery failed: {e_inner}")
        
        if not key:
            # Elite V2.2: Emergency fallback to 2.0-flash-lite for discovery
            try:
                key = await self.rotator.get_key(model_name="gemini-2.0-flash-lite")
            except:
                logger.warning("[TrinityModels] No keys available for discovery. AI services may be degraded.")
                return []

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    all_models = resp.json().get("models", [])
                    models = []
                    for m in all_models:
                        name = m.get("name", "")
                        short = name.replace("models/", "")
                        methods = m.get("supportedGenerationMethods") or []
                        
                        # Gate 1: Must support generateContent
                        if "generateContent" not in methods:
                            continue
                        # Gate 2: Hard blacklist (no function calling, unstable, etc.)
                        if any(hbl in name for hbl in HARD_BLACKLIST):
                            continue
                        # Gate 3: DB-configurable blacklist
                        if any(bl in name for bl in self._config.get("blacklist", [])):
                            continue
                            
                        # Elite V2.2: Store metadata signals for intelligent ranking
                        metadata = {
                            "inputTokenLimit": m.get("inputTokenLimit", 128000),
                            "outputTokenLimit": m.get("outputTokenLimit", 4096),
                            "displayName": m.get("displayName", ""),
                            "version": m.get("version", "")
                        }
                        await self.rotator.save_model_metadata(short, metadata)
                        
                        # Elite V2.2: Auto-assign capability for modern architectures
                        if any(x in short.lower() for x in ["pro", "ultra", "brain", "2.0", "2.5", "3.0", "3.1", "flash"]):
                            current_cap = await self.rotator.get_model_capability(short)
                            
                            # Refined Hierarchy: 3.x and 2.5-pro are ELITE. Others (2.0, 2.5-flash, 1.5-pro) are AGENTIC.
                            target_cap = "AGENTIC"
                            if any(v in short for v in ["3.1", "3.0", "ultra"]):
                                target_cap = "ELITE"
                            elif "2.5" in short and "pro" in short:
                                target_cap = "ELITE"

                            if current_cap != target_cap:
                                await self.rotator.mark_model_capability(short, target_cap)
                                logger.info(f"[TrinityModels] Sync-promoted {short} to {target_cap} (was {current_cap})")

                        models.append(short)
                    
                    # Elite V2.2: Hard-inject CNS models if missing from Google API list
                    cns_models = [self.default_model, self.fallback_model, "gemini-2.0-flash", "gemini-2.0-flash-lite"]
                    for cns in cns_models:
                        if cns not in [m.get("name", "").replace("models/", "") for m in all_models]:
                            if any(hbl in cns for hbl in HARD_BLACKLIST): continue
                            if cns not in models:
                                models.append(cns)
                            # Ensure we have some default metadata
                            await self.rotator.save_model_metadata(cns, {
                                "inputTokenLimit": 1048576,
                                "outputTokenLimit": 8192,
                                "displayName": f"CNS Force: {cns}",
                                "version": "v1beta"
                            })
                            await self.rotator.mark_model_capability(cns, "AGENTIC")

                    # Sort by score so best models are tried first
                    models.sort(key=lambda x: self._score_model_sync(x), reverse=True)
                    logger.info(f"[TrinityModels] Discovered {len(models)} valid models (top 5): {models[:5]}")
                    await self.rotator.save_discovered_models(models)
                    return models
        except Exception as e:
            logger.error(f"[TrinityModels] Discovery failed: {e}")
        return []

    def _score_model_sync(self, model_name: str) -> int:
        """Elite V2.2: Universal Model Scoring based on Metadata Signals."""
        m = model_name.lower()
        score = 0
        
        # 0. Hard Blacklist Guard
        if any(hbl in m for hbl in HARD_BLACKLIST):
            return -10000

        # 1. Version Tier (The most important factor in 2026)
        # Modern Architecture Scoring (Elite V2.2)
        if "3.1" in m: score += 2500
        elif "3" in m: score += 2000
        elif "2.5" in m: score += 1500
        elif "2.0" in m: score += 1000

        # Tier Differentiation
        if "-pro" in m: score += 300
        if "-flash" in m: score += 100
        if "-lite" in m: score -= 200
        
        # Elite V2.2: Free Tier Prioritization (Sếp's Order - CNS V89.5)
        # Ưu tiên các model có Quota lớn hoặc là 'Điểm ngọt' trước để tiết kiệm Pro Quota.
        if "gemini-2.0-flash" in m: score += 7000       # "Bao la" nhất (2026 Rank 1)
        elif "gemini-2.0-pro" in m: score += 6000      # Mạnh nhất (Rank 2)
        elif "gemini-2.0-flash-lite" in m: score += 5000 # Tiết kiệm (Rank 3)
        
        # 2. Model Grade (Brain vs Fast)
        if "pro" in m: score += 200
        elif "ultra" in m: score += 400
        elif "flash" in m: score += 100
        
        # 3. Special Features
        if "customtools" in m: score += 50
        
        # 4. Stability Signals (Preview/Lite)
        # Elite V2.2: Reduced penalties for modern previews as requested by Sếp.
        if "preview" in m: score -= 20
        if "lite" in m: score -= 100
        
        return score

    async def _score_model_async(self, model_name: str) -> int:
        """Elite V2.2: Enhanced scoring incorporating Real-time Capability (ELITE/AGENTIC)."""
        base_score = self._score_model_sync(model_name)
        
        # Add Capability Bonus
        cap = await self.rotator.get_model_capability(model_name)
        if cap == "ELITE": base_score += 500
        elif cap == "AGENTIC": base_score += 200
        elif cap == "LEGACY": base_score -= 100
        
        # Add Context Window Signal (Data-driven)
        meta = await self.rotator.get_model_metadata(model_name)
        ctx = int(meta.get("inputTokenLimit", 128000))
        base_score += int((ctx / 128000) * 10) # 1M context = +78 points
        
        return base_score

    async def get_role_models(self, role: str, discovered: list[str]) -> list[str]:
        if not discovered: return []
        
        patterns = self._config.get("role_patterns", {}).get(role, [])
        blacklist = self._config.get("blacklist", [])
        lockdown = self._config.get("lockdown", [])
            
        # First filter: Only compatible and non-blacklisted
        candidates = [
            m for m in discovered 
            if any(p in m.lower() for p in patterns)
            and "experimental" not in m.lower() 
            and not any(l in m.lower() for l in lockdown)
            and not any(bl in m.lower() for bl in blacklist)
        ]

        # Elite V2.2: Hard filter for Brain role (Must support tools/signals)
        # R110: Allow Flash models in Brain role if they are verified AGENTIC/ELITE.
        if role == self.ROLE_BRAIN:
            verified = []
            for m in candidates:
                cap = await self.rotator.get_model_capability(m)
                if cap in ["AGENTIC", "ELITE"]:
                    verified.append(m)
            candidates = verified
        
        # Second filter: Sort by Elite V2.2 Score (Best to Worst)
        # We need to collect scores first because _score_model_async is awaitable
        scored_candidates = []
        for m in candidates:
            score = await self._score_model_async(m)
            scored_candidates.append((m, score))
            
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return [x[0] for x in scored_candidates]

    async def build_chain(self, role: Optional[str], db_primary: str, db_waterfall: list[str], discovered: list[str]) -> list[str]:
        await self._ensure_config()
        seen: set[str] = set()
        raw: list[str] = []
        
        def _add(m: str) -> None:
            if m and m not in seen:
                seen.add(m)
                raw.append(m)
        
        # Priority 1: DB-configured models (user's explicit choice)
        if db_primary: _add(db_primary)
        for m in db_waterfall: _add(m)
        
        # Priority 2: Role-specific discovered models (already scored & sorted)
        if role:
            for m in await self.get_role_models(role, discovered): _add(m)
            # Also add the complementary role as fallback
            alt_role = self.ROLE_FAST if role == self.ROLE_BRAIN else self.ROLE_BRAIN
            for m in await self.get_role_models(alt_role, discovered): _add(m)
        else:
            for m in await self.get_role_models(self.ROLE_BRAIN, discovered): _add(m)
            for m in await self.get_role_models(self.ROLE_FAST, discovered): _add(m)
        
        # Priority 3: Env defaults as last resort
        _add(self.default_model)
        _add(self.fallback_model)

        # Filter: Remove blacklisted, locked, and poisoned models
        blacklist = self._config.get("blacklist", [])
        lockdown = self._config.get("lockdown", [])
        
        healthy: list[str] = []
        for m in raw:
            if any(bl in m for bl in blacklist) or any(hbl in m for hbl in HARD_BLACKLIST):
                continue
            if any(l in m for l in lockdown):
                continue
            if not await self.rotator.is_model_poisoned(m):
                healthy.append(m)
        
        # Fail-safe: ensure we have AT LEAST the defaults (Force Hardcoded Stable)
        if not healthy:
            for m in ["gemini-2.0-flash", "gemini-2.0-pro", self.default_model, self.fallback_model]:
                if not await self.rotator.is_model_poisoned(m) and not self.is_blacklisted(m):
                    healthy.append(m)

        return healthy

    def classify_error(self, err: str) -> str:
        err = err.lower()
        mapping = self._config.get("error_mapping", DEFAULT_AI_CONFIG["error_mapping"])
        
        for cat, patterns in mapping.items():
            if any(p in err for p in patterns):
                # Special cases or overrides
                if "tool output is not supported" in err: return "tool_unsupported"
                if "interactions api" in err: return "rate_limit"
                return cat
                
        return "unknown"

    def is_daily_quota(self, err: str) -> bool:
        """Elite V2.2: Phân biệt chính xác hạn mức ngày vs hạn mức phút."""
        err_lower: str = err.lower()
        # Nếu có chữ 'per minute' hoặc 'per minute per user' thì CHẮC CHẮN không phải daily
        if "per minute" in err_lower:
            return False
        return any(p in err_lower for p in ["daily", "per_day", "requests_per_day", "generaterequestsperdayperproject"])

    def is_blacklisted(self, model_name: str) -> bool:
        """Elite V2.2: Martial Law verification."""
        m = model_name.lower()
        # 1. Hard Blacklist (Kernel level)
        if any(hbl in m for hbl in HARD_BLACKLIST):
            return True
        # 2. Configurable Blacklist (DB level)
        if any(bl in m for bl in self._config.get("blacklist", [])):
            return True
        return False

