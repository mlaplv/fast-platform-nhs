from __future__ import annotations
import logging
import json
import os
import uuid
from typing import Dict, List, Optional, Union
from litestar import Controller, post, get, delete, Request
from litestar.di import Provide
from litestar.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from backend.schemas.voice import (
    VoiceSettingsPayload, VoiceSettingsResponse, CapabilityMetadata,
    CampaignModePayload, LexiconOverridePayload, LexiconStopwordPayload,
    CampaignModeResponse, LexiconOverridesResponse,
    LexiconStopwordsResponse
)
from backend.schemas.common import SuccessResponse
from backend.services.settings_service import settings_service
from backend.guards import PermissionGuard


logger = logging.getLogger("api-gateway")


class SettingsController(Controller):
    """
    R2 (V30.0): Strict Class-based Controller for Administrative Settings.
    Manages per-user configurations for Voice Identity and Cognitive Capabilities.
    """
    path = "/api/v1/settings"
    guards = [PermissionGuard("system:all")]

    @get("/voice")
    async def get_voice_settings(self, db_session: "AsyncSession", request: Request) -> VoiceSettingsResponse:
        """Fetch current voice and cognitive settings (Zero-Hydration)."""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return await settings_service.get_voice_settings(db_session, user_info["sub"])

    @post("/voice")
    async def update_voice_settings(
        self, db_session: "AsyncSession", request: Request, data: VoiceSettingsPayload
    ) -> SuccessResponse:
        """Update user voice identity and cognitive settings (Surgical Update)."""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        res = await settings_service.update_voice_settings(db_session, user_info["sub"], data)
        await db_session.commit()
        return res

    @get("/campaign-mode", dependencies={})
    async def get_campaign_mode(self, request: Request) -> CampaignModeResponse:
        """Fetch global Campaign Mode state (delegated to service)."""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return await settings_service.get_campaign_mode()

    @post("/campaign-mode", dependencies={})
    async def toggle_campaign_mode(self, request: Request, data: CampaignModePayload) -> SuccessResponse:
        """Toggle global Campaign Mode state in Redis"""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return await settings_service.toggle_campaign_mode(data.is_campaign_mode, user_info["sub"])

    # ═══════════════════════════════════════════════════════
    # SYSTEM LEXICON: Dynamic Dicts (2026 Microservices)
    # ═══════════════════════════════════════════════════════

    @get("/lexicon/overrides")
    async def get_lexicon_overrides(self, request: Request) -> LexiconOverridesResponse:
        """Fetch system-wide STT Overrides"""
        return await settings_service.get_lexicon_overrides()

    @post("/lexicon/overrides")
    async def add_lexicon_override(self, request: Request, data: LexiconOverridePayload) -> SuccessResponse:
        """Add or update a system-wide STT Override"""
        return await settings_service.add_lexicon_override(data)

    @delete("/lexicon/overrides/{wrong_word:str}", status_code=200)
    async def delete_lexicon_override(self, request: Request, wrong_word: str) -> SuccessResponse:
        """Delete a system-wide STT Override"""
        return await settings_service.delete_lexicon_override(wrong_word)

    @get("/lexicon/stopwords")
    async def get_lexicon_stopwords(self, request: Request) -> LexiconStopwordsResponse:
        """Fetch system-wide Stopwords (Filler words)"""
        return await settings_service.get_lexicon_stopwords()

    @post("/lexicon/stopwords")
    async def add_lexicon_stopword(self, request: Request, data: LexiconStopwordPayload) -> SuccessResponse:
        """Add a Stopword to the system"""
        return await settings_service.add_lexicon_stopword(data.word)

    @delete("/lexicon/stopwords/{word:str}", status_code=200)
    async def delete_lexicon_stopword(self, request: Request, word: str) -> SuccessResponse:
        """Delete a Stopword from the system"""
        return await settings_service.delete_lexicon_stopword(word)


