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

DEFAULT_AI_CONFIG = {
    "role_patterns": {
        "fast": ["flash", "8b", "lite"],
        "brain": ["pro", "ultra", "brain"]
    },
    "blacklist": ["-tts", "-embedding", "-aqa", "-image", "-vision", "deep-research", "robotics", "lyria", "banana"],
    "lockdown": ["early-access", "alpha", "customtools"], # Gỡ bỏ 'preview' vì 2026 đa số là bản preview ổn định
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
                # We try one of the known broad-quota models or just the default
                key = await self.rotator.get_key(model_name="gemini-1.5-flash")
            except Exception as e_inner:
                logger.warning(f"[TrinityModels] Full key discovery failed: {e_inner}")
        
        if not key:
            logger.warning("[TrinityModels] No keys available for discovery. AI services may be degraded.")
            return []

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    models = [
                        m.get("name", "").replace("models/", "") for m in resp.json().get("models", [])
                        if m.get("name")
                        and "generateContent" in (m.get("supportedGenerationMethods") or [])
                        and not any(bl in m.get("name", "") for bl in self._config.get("blacklist", []))
                    ]
                    await self.rotator.save_discovered_models(models)
                    return models
        except Exception as e:
            logger.error(f"[TrinityModels] Discovery failed: {e}")
        return []

    def _score_model(self, model_name: str) -> int:
        """Elite V2.2: Universal Model Scoring for Vietnam & Standard API."""
        m = model_name.lower()
        score = 0
        
        # 1. Version Tier (The most important factor in 2026)
        if "3.1" in m: score += 1000
        elif "3" in m: score += 900
        elif "2.5" in m: score += 800
        elif "2.0" in m: score += 700
        elif "1.5" in m: score += 600
        
        # 2. Model Grade (Brain vs Fast)
        if "pro" in m: score += 100
        elif "ultra" in m: score += 200 # Ultra is rare but supreme
        elif "flash" in m: score += 50
        
        # 3. Special Features
        if "customtools" in m: score += 10 # Better tool support
        
        # 4. Penalty for non-standard/experimental
        if "experimental" in m: score -= 50
        if "alpha" in m or "beta" in m: score -= 30
        
        return score

    def get_role_models(self, role: str, discovered: list[str]) -> list[str]:
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
        
        # Second filter: Sort by Elite V2.2 Score (Best to Worst)
        candidates.sort(key=lambda x: self._score_model(x), reverse=True)
        return candidates

    async def build_chain(self, role: Optional[str], db_primary: str, db_waterfall: list[str], discovered: list[str]) -> list[str]:
        await self._ensure_config()
        raw = []
        if db_primary: raw.append(db_primary)
        for m in (db_waterfall + [self.default_model, self.fallback_model] + self.get_role_models(self.ROLE_BRAIN, discovered) + self.get_role_models(self.ROLE_FAST, discovered)):
            if m and m not in raw: raw.append(m)

        if role:
            kw = ["lite", "8b", "flash"] if role == self.ROLE_FAST else ["pro", "ultra", "brain", "creative"]
            prio = [m for m in raw if any(k in m.lower() for k in kw)]
            raw = prio + [m for m in raw if m not in prio]

        healthy = []
        blacklist = self._config.get("blacklist", [])
        lockdown = self._config.get("lockdown", [])
        
        for m in raw:
            # Elite V2.2: Double-safety — strip blacklisted model types even if they snuck into discovered.
            if any(bl in m for bl in blacklist):
                logger.debug(f"[TrinityModels] Skipping blacklisted model: {m}")
                continue
            
            # Elite V2.2: Universal lockdown for experimental models in standard production flows
            if any(l in m for l in lockdown):
                logger.debug(f"[TrinityModels] Skipping experimental/locked model in production chain: {m}")
                continue
            if not await self.rotator.is_model_poisoned(m):
                healthy.append(m)
        
        # Elite V2.2: Fail-safe - ensure we have AT LEAST the defaults if everything else failed
        if not healthy:
            for m in [self.default_model, self.fallback_model]:
                if not await self.rotator.is_model_poisoned(m):
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
        return any(p in err.lower() for p in ["daily", "per_day", "requests_per_day", "generaterequestsperdayperproject"])
