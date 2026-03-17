import logging
import time
from typing import List, Dict, Optional
from litestar import Controller, get, post, Request
from litestar.exceptions import NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.voice_service import voice_service
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

class KeyStats(BaseModel):
    index: int
    key_preview: str
    fail_count: int
    health_score: int
    last_used: float
    status: str

class BulkKeyInput(BaseModel):
    keys: str

class ModelConfig(BaseModel):
    primary_model: Optional[str] = None
    ai_models: List[str] = []

class AIController(Controller):
    """
    [ADMIN ONLY] AI Engine Configuration & Monitoring (ELITE V2.2).
    """
    path = "/api/v1/admin/ai"
    tags = ["AI Management"]

    @get("/keys")
    async def get_all_key_stats(self) -> List[KeyStats]:
        """Returns real-time metrics for all Gemini keys."""
        all_keys = key_rotator.keys
        stats = []
        now = time.time()

        for idx, key in enumerate(all_keys):
            kid = key_rotator._get_key_id(key)
            meta = await key_rotator.client.hgetall(f"{key_rotator.METADATA_PREFIX}{kid}")
            is_blacklisted = await key_rotator.client.exists(f"{key_rotator.BLACKLIST_PREFIX}{kid}")

            fail_count = int(meta.get("fail_count", 0))
            last_used = float(meta.get("last_used", 0))

            status = "ACTIVE"
            if is_blacklisted:
                status = "DEAD"
            elif fail_count > 0:
                cooldown = min(key_rotator.BASE_COOLDOWN * (2 ** (fail_count - 1)), key_rotator.MAX_COOLDOWN)
                if now - last_used < cooldown:
                    status = "COOLDOWN"

            stats.append(KeyStats(
                index=idx,
                key_preview=f"{key[:8]}...{key[-4:]}",
                fail_count=fail_count,
                health_score=int(meta.get("health_score", 100)),
                status=status,
                last_used=last_used
            ))
        return stats

    @post("/keys/reset")
    async def reset_all_keys(self) -> Dict[str, object]:
        """Reset ALL key health states via key_rotator."""
        if not key_rotator._use_redis or not key_rotator.client:
            return {"status": "error", "message": "Redis unavailable"}

        try:
            cleared = await key_rotator.reset_health()
            return {"status": "success", "cleared": cleared, "message": "Đã reset hệ thống Key và nạp lại từ DB."}
        except Exception as e:
            logger.exception(f"[AIController] Reset failed: {e}")
            return {"status": "error", "message": str(e)}

    @post("/keys/bulk")
    async def sync_bulk_keys(self, request: Request, db_session: AsyncSession, data: BulkKeyInput) -> Dict[str, object]:
        """Bulk upload and save Gemini keys via VoiceService."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise NotAuthorizedException("User session required")

        new_keys = [k.strip() for k in data.keys.replace(",", "\n").split("\n") if k.strip()]
        if not new_keys:
             return {"status": "error", "message": "No valid keys found"}

        try:
            count = await voice_service.update_gemini_keys(db_session, user_info["id"], new_keys)
            return {
                "status": "success",
                "count": count,
                "message": f"Successfully updated {count} keys."
            }
        except Exception as e:
            logger.exception(f"[AIController] Bulk sync failed: {e}")
            return {"status": "error", "message": str(e)}

    @get("/models/discover")
    async def discover_models(self, request: Request, db_session: AsyncSession) -> Dict[str, object]:
        """Discover models via VoiceService."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise NotAuthorizedException("User session required")

        try:
            models = await voice_service.discover_models(db_session, user_info["id"])
            return {"status": "success", "models": models}
        except Exception as e:
            logger.error(f"[AIController] Discovery failed: {e}")
            return {"status": "error", "message": str(e)}

    @get("/models")
    async def get_ai_models(self, request: Request, db_session: AsyncSession) -> Dict[str, object]:
        """Returns the current model waterfall configuration."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise NotAuthorizedException("User session required")

        profile = await voice_service.get_or_create_profile(db_session, user_info["id"])

        return {
            "primary_model": profile.primary_model or trinity_bridge.default_model_name,
            "ai_models": profile.ai_models or trinity_bridge.model_waterfall,
            "discovered_models": profile.discovered_models or []
        }

    @post("/models")
    async def update_ai_models(self, request: Request, db_session: AsyncSession, data: ModelConfig) -> Dict[str, str]:
        """Update the AI model waterfall configuration via VoiceService."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise NotAuthorizedException("User session required")

        await voice_service.update_model_config(
            db_session,
            user_info["id"],
            data.primary_model,
            data.ai_models
        )

        return {"status": "success", "message": "Model configuration updated and hot-reloaded."}

    @post("/test/{index:int}")
    async def test_key(self, index: int) -> Dict[str, str]:
        """Manually trigger a health check for a specific key."""
        if index < 0 or index >= len(key_rotator.keys):
            return {"status": "error", "message": "Invalid index"}

        key = key_rotator.keys[index]
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
                resp = await client.post(url, json={"contents": [{"parts":[{"text": "ping"}]}]})

                if resp.status_code == 200:
                    await key_rotator.set_success(key)
                    return {"status": "success", "message": "Key is healthy"}
                else:
                    await key_rotator.mark_unhealthy(key, reason=f"HTTP_{resp.status_code}")
                    return {"status": "error", "message": f"Ping failed with status {resp.status_code}"}
        except Exception as e:
            await key_rotator.mark_unhealthy(key, reason=str(e))
            return {"status": "error", "message": str(e)}
