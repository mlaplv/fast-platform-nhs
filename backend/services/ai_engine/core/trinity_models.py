from __future__ import annotations
import logging
import httpx
from typing import Optional

logger = logging.getLogger("api-gateway")

class TrinityModels:
    """Helper for model discovery and chain building (V76)."""
    
    def __init__(self, rotator: 'KeyRotator', default_model: str, fallback_model: str) -> None:
        self.rotator: 'KeyRotator' = rotator
        self.default_model: str = default_model
        self.fallback_model: str = fallback_model
        self.ROLE_FAST: str = "fast"
        self.ROLE_BRAIN: str = "brain"

    async def discover_available(self) -> list[str]:
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
                    models = [m["name"].replace("models/", "") for m in resp.json().get("models", []) 
                             if "generateContent" in (m.get("supportedGenerationMethods") or [])]
                    await self.rotator.save_discovered_models(models)
                    return models
        except Exception as e:
            logger.error(f"[TrinityModels] Discovery failed: {e}")
        return []

    def get_role_models(self, role: str, discovered: list[str]) -> list[str]:
        if not discovered: return []
        potential = ["flash-lite", "flash-8b", "flash"] if role == self.ROLE_FAST else ["pro", "brain"]
        res = [m for p in potential for m in discovered if p in m.lower()]
        res.sort(reverse=True)
        return res

    async def build_chain(self, role: Optional[str], db_primary: str, db_waterfall: list[str], discovered: list[str]) -> list[str]:
        raw = []
        if db_primary: raw.append(db_primary)
        for m in (db_waterfall + [self.default_model, self.fallback_model] + self.get_role_models(self.ROLE_BRAIN, discovered) + self.get_role_models(self.ROLE_FAST, discovered)):
            if m and m not in raw: raw.append(m)

        if role:
            kw = ["lite", "8b", "flash"] if role == self.ROLE_FAST else ["pro", "ultra", "brain", "creative"]
            prio = [m for m in raw if any(k in m.lower() for k in kw)]
            raw = prio + [m for m in raw if m not in prio]

        healthy = []
        for m in raw:
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
        if any(p in err for p in ["api key not valid", "invalid_key", "key_expired", "project disabled", "deleted"]): return "auth_hard"
        
        # Elite V2.2: 403 Forbidden is often regional or model-specific, treat as SOFT unless repeated
        if any(p in err for p in ["401", "403", "unauthorized", "forbidden", "permission_denied", "user_location_not_supported"]): return "auth_soft"
        
        # Elite V2.2: Deep Research models in preview might not support standard generateContent
        if "interactions api" in err: return "rate_limit" # Force fallback to next model
        
        if any(p in err for p in ["context_length_exceeded", "too many tokens", "safety", "blocked", "invalid_argument", "400"]): return "fail_fast"
        if "tool output is not supported" in err: return "tool_unsupported"
        if any(p in err for p in ["429", "quota", "rate limit", "limit reached", "resource_exhausted", "503", "unavailable", "500", "reset by peer", "deadline_exceeded"]): return "rate_limit"
        if "model not found" in err or "404" in err: return "model_not_found"
        return "unknown"

    def is_daily_quota(self, err: str) -> bool:
        return any(p in err.lower() for p in ["daily", "per_day", "requests_per_day", "generaterequestsperdayperproject"])
