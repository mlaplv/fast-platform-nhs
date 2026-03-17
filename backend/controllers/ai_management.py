import logging
import time
from typing import List, Dict, Optional
from litestar import Controller, get, post, Request
from litestar.exceptions import NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.services.ai_engine.key_rotator import key_rotator
from backend.services.voice_service import voice_service
from backend.services.ai_engine.trinity_bridge import trinity_bridge

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
    async def get_all_key_stats(self) -> List[Dict[str, object]]:
        """Returns real-time metrics for all Gemini keys."""
        return await voice_service.get_key_stats()

    @post("/keys/reset")
    async def reset_all_keys(self) -> Dict[str, object]:
        """Reset ALL key health states via key_rotator."""
        try:
            return await voice_service.reset_health()
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

        return await voice_service.get_model_config(db_session, user_info["id"])

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
        return await voice_service.test_key(index)
