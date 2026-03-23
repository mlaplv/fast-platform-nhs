import logging
import httpx
from typing import List, Optional

logger = logging.getLogger("api-gateway")

class TrinityModels:
    """Helper for model discovery and chain building (V76)."""
    
    def __init__(self, rotator, default_model: str, fallback_model: str):
        self.rotator = rotator
        self.default_model = default_model
        self.fallback_model = fallback_model
        self.ROLE_FAST = "fast"
        self.ROLE_BRAIN = "brain"

    async def discover_available(self) -> List[str]:
        cached = await self.rotator.get_discovered_models()
        if cached: return cached

        key = await self.rotator.get_key(model_name=self.default_model)
        if not key: return []

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

    def get_role_models(self, role: str, discovered: List[str]) -> List[str]:
        if not discovered: return []
        potential = ["flash-lite", "flash-8b", "flash"] if role == self.ROLE_FAST else ["pro", "brain"]
        res = [m for p in potential for m in discovered if p in m.lower()]
        res.sort(reverse=True)
        return res

    async def build_chain(self, role: Optional[str], db_primary: str, db_waterfall: List[str], discovered: List[str]) -> List[str]:
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
            if not await self.rotator.is_model_poisoned(m): healthy.append(m)
        return healthy

    def classify_error(self, err: str) -> str:
        err = err.lower()
        if any(p in err for p in ["401", "403", "api key not valid", "invalid_key", "key_expired", "project disabled", "deleted"]): return "auth"
        if any(p in err for p in ["context_length_exceeded", "too many tokens", "safety", "blocked", "invalid_argument", "400"]): return "fail_fast"
        if "tool output is not supported" in err: return "tool_unsupported"
        if any(p in err for p in ["429", "quota", "rate limit", "limit reached", "resource_exhausted", "503", "unavailable", "500"]): return "rate_limit"
        if "model not found" in err or "404" in err: return "model_not_found"
        return "unknown"

    def is_daily_quota(self, err: str) -> bool:
        return any(p in err.lower() for p in ["daily", "per_day", "requests_per_day", "generaterequestsperdayperproject"])
