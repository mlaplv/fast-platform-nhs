from __future__ import annotations
import logging
import time
import uuid
from typing import List, Dict, Optional
from litestar import Controller, get, post, Request
from litestar.exceptions import NotAuthorizedException, HTTPException
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.ai_service import ai_service
from backend.schemas.common import SuccessResponse
from backend.schemas.ai import (
    KeyStats, BulkKeyInput, ModelConfig, AIModelStatusResponse,
    ModelDiscoveryResponse
)

from backend.guards import PermissionGuard

logger = logging.getLogger("api-gateway")

class AIController(Controller):
    """
    [ADMIN ONLY] AI Engine Configuration & Monitoring.
    """
    path = "/api/v1/admin/ai"
    guards = [PermissionGuard("sys:admin")]
    tags = ["AI Management"]

    @get("/keys")
    async def get_all_key_stats(self) -> List[KeyStats]:
        """Returns real-time metrics for all Gemini keys."""
        return await ai_service.get_all_key_stats()

    @post("/keys/reset")
    async def reset_all_keys(self) -> SuccessResponse:
        """Reset ALL key health states (clear blacklist + cooldowns). Safe to call anytime."""
        return await ai_service.reset_all_keys()

    @post("/keys/bulk")
    async def sync_bulk_keys(self, request: Request, db_session: "AsyncSession", data: BulkKeyInput) -> SuccessResponse:
        """Bulk upload and save Gemini keys (Surgical Update)."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise HTTPException(status_code=401, detail="User session required")

        res = await ai_service.sync_bulk_keys(db_session, user_info["id"], data)
        await db_session.commit()
        return res

    @get("/models/discover")
    async def discover_models(self, request: Request, db_session: "AsyncSession") -> ModelDiscoveryResponse:
        """Fetch available Gemini models directly from Google API and persist (Surgical)."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise HTTPException(status_code=401, detail="User session required")

        res = await ai_service.discover_models(db_session, user_info["id"])
        await db_session.commit()
        return res

    @get("/models")
    async def get_ai_models(self, request: Request, db_session: "AsyncSession") -> AIModelStatusResponse:
        """Returns the current model waterfall (Scalar Projection Rule 1.5)."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise HTTPException(status_code=401, detail="User session required")

        return await ai_service.get_ai_models(db_session, user_info["id"])

    @post("/models")
    async def update_ai_models(self, request: Request, db_session: "AsyncSession", data: ModelConfig) -> SuccessResponse:
        """Update the AI model waterfall configuration (Surgical Update)."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise HTTPException(status_code=401, detail="User session required")

        res = await ai_service.update_ai_models(db_session, user_info["id"], data)
        await db_session.commit()
        return res

    @post("/test/{index:int}")
    async def test_key(self, index: int) -> SuccessResponse:
        """Manually trigger a health check for a specific key."""
        return await ai_service.test_key(index)
