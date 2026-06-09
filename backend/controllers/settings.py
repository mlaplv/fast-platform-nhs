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
from backend.schemas.system_settings import SystemSettingsPayload, SystemSettingsResponse
from backend.schemas.common import SuccessResponse
from backend.services.settings_service import settings_service
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum


logger = logging.getLogger("api-gateway")


class SettingsController(Controller):
    """
    R2 (V30.0): Strict Class-based Controller for Administrative Settings.
    Manages per-user configurations for Voice Identity and Cognitive Capabilities.
    """
    path = "/api/v1/settings"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

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

    @get("/general")
    async def get_general_settings(self, db_session: "AsyncSession") -> SystemSettingsResponse:
        """Fetch global system settings."""
        return await settings_service.get_general_settings(db_session)

    @post("/general")
    async def update_general_settings(
        self, db_session: "AsyncSession", data: SystemSettingsPayload
    ) -> SuccessResponse:
        """Update global system settings."""
        res = await settings_service.update_general_settings(db_session, data)
        await db_session.commit()
        return res

    @get("/notification-retention")
    async def get_notification_retention(self, db_session: "AsyncSession") -> dict:
        """Fetch notification retention configuration."""
        from backend.database.models.system import SystemSetting
        stmt = select(SystemSetting).where(SystemSetting.key == "notification_retention")
        setting = (await db_session.execute(stmt)).scalar_one_or_none()
        if not setting or not isinstance(setting.value, dict):
            return {"soft_delete_days": 7, "hard_delete_days": 14}
        return {
            "soft_delete_days": setting.value.get("soft_delete_days", 7),
            "hard_delete_days": setting.value.get("hard_delete_days", 14)
        }

    @post("/notification-retention")
    async def update_notification_retention(
        self, db_session: "AsyncSession", data: dict
    ) -> SuccessResponse:
        """Update notification retention configuration."""
        from backend.database.models.system import SystemSetting
        
        soft_days = int(data.get("soft_delete_days", 7))
        hard_days = int(data.get("hard_delete_days", 14))
        
        stmt = select(SystemSetting).where(SystemSetting.key == "notification_retention")
        res = await db_session.execute(stmt)
        setting = res.scalar_one_or_none()
        
        if not setting:
            setting = SystemSetting(key="notification_retention", value={})
            db_session.add(setting)
            
        setting.value = {
            "soft_delete_days": soft_days,
            "hard_delete_days": hard_days
        }
        await db_session.commit()
        
        # Invalidate/Sync to Redis if needed for job performance
        from backend.services.xohi_memory import xohi_memory
        await xohi_memory.client.set("system:notification_retention", json.dumps(setting.value))
        
        return SuccessResponse(ok=True, id="notification_retention")

    @get("/loyalty-checkin")
    async def get_loyalty_checkin_config(self, db_session: "AsyncSession") -> dict:
        """Fetch daily check-in configuration."""
        from backend.services.commerce.loyalty import LoyaltyService
        return await LoyaltyService._get_checkin_config(db_session)

    @post("/loyalty-checkin")
    async def update_loyalty_checkin_config(
        self, db_session: "AsyncSession", data: dict
    ) -> SuccessResponse:
        """Update daily check-in configuration."""
        from backend.database.models.system import SystemSetting
        
        cycle_days = data.get("cycle_days", 7)
        rewards = data.get("rewards", [1] * cycle_days)
        is_active = data.get("is_active", True)
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        points_expiration_days = data.get("points_expiration_days", 30)
        
        if len(rewards) != cycle_days:
            raise HTTPException(status_code=400, detail="Rewards array size must match cycle days count")
            
        stmt = select(SystemSetting).where(SystemSetting.key == "LOYALTY_CHECKIN_CONFIG")
        res = await db_session.execute(stmt)
        setting = res.scalar_one_or_none()
        
        if not setting:
            setting = SystemSetting(key="LOYALTY_CHECKIN_CONFIG", value={})
            db_session.add(setting)
            
        setting.value = {
            "cycle_days": cycle_days,
            "rewards": rewards,
            "is_active": is_active,
            "start_date": start_date,
            "end_date": end_date,
            "points_expiration_days": points_expiration_days
        }
        await db_session.commit()
        return SuccessResponse(ok=True, id="LOYALTY_CHECKIN_CONFIG")



