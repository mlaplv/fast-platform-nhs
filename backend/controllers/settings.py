import logging
import json
import os
import uuid
from typing import Dict, List, Optional, Union
from litestar import Controller, post, get, delete, Request
from litestar.di import Provide
from litestar.exceptions import HTTPException
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from backend.schemas.voice import (
    VoiceSettingsPayload, VoiceSettingsResponse, CapabilityMetadata, 
    CampaignModePayload, LexiconOverridePayload, LexiconStopwordPayload
)
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.user_service import user_service
from backend.services.voice_service import voice_service
from backend.database.models import User, VoiceProfile
from backend.constants.voice import DEFAULT_GREETING, DEFAULT_FAREWELL
from backend.utils.text import normalize_vn
from backend.services.capability_registry import capability_registry
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
    async def get_voice_settings(self, db_session: AsyncSession, request: Request) -> Dict[str, object]:
        """Fetch current voice and cognitive settings (Dynamic Matrix)"""
        user_info = getattr(request.state, "user", None)
        if not user_info or "id" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return await voice_service.get_voice_settings(db_session, user_info["id"])

    @post("/voice")
    async def update_voice_settings(
        self, db_session: AsyncSession, request: Request, data: VoiceSettingsPayload
    ) -> dict:
        """
        [MẶT TRẬN 4] - Dynamic Per-User Setup using services
        """
        user_info = getattr(request.state, "user", None)
        if not user_info or "id" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user_id = user_info["id"]

        result = await voice_service.update_voice_settings(
            db_session,
            user_id,
            data.model_dump()
        )

        return {
            "status": "success",
            "message": "Đã cập nhật bộ nhận diện giọng nói cho sếp.",
            "data": result
        }

    @get("/campaign-mode", dependencies={})
    async def get_campaign_mode(self, request: Request) -> dict:
        """Fetch global Campaign Mode state from Redis"""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        from backend.services.xohi_memory import xohi_memory
        val = await xohi_memory.client.get("system:campaign_mode")
        is_campaign = val == "1"
        return {"is_campaign_mode": is_campaign}

    @post("/campaign-mode", dependencies={})
    async def toggle_campaign_mode(self, request: Request, data: CampaignModePayload) -> dict:
        """Toggle global Campaign Mode state in Redis"""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        from backend.services.xohi_memory import xohi_memory
        val = "1" if data.is_campaign_mode else "0"
        await xohi_memory.client.set("system:campaign_mode", val)
        
        status_msg = "BẬT" if data.is_campaign_mode else "TẮT"
        logger.info(f"[Settings] User {user_info['sub']} toggled Campaign Mode: {data.is_campaign_mode}")
        
        return {
            "status": "success",
            "message": f"Đã {status_msg} chế độ Chiến Dịch Quảng Cáo.",
            "is_campaign_mode": data.is_campaign_mode
        }

    # ═══════════════════════════════════════════════════════
    # SYSTEM LEXICON: Dynamic Dicts (2026 Microservices)
    # ═══════════════════════════════════════════════════════

    @get("/lexicon/overrides")
    async def get_lexicon_overrides(self, request: Request) -> dict:
        """Fetch system-wide STT Overrides"""
        from backend.services.xohi_memory import xohi_memory
        overrides = await xohi_memory.get_system_stt_overrides()
        return {"overrides": overrides}

    @post("/lexicon/overrides")
    async def add_lexicon_override(self, request: Request, data: LexiconOverridePayload) -> dict:
        """Add or update a system-wide STT Override"""
        from backend.services.xohi_memory import xohi_memory
        mapping = {data.wrong_word.strip().lower(): data.right_word.strip()}
        await xohi_memory.set_system_stt_overrides(mapping)
        logger.info(f"[Lexicon] Added override '{data.wrong_word}' -> '{data.right_word}'")
        return {"status": "success", "message": f"Đã thêm luật nắn lỗi: {data.wrong_word} ➔ {data.right_word}"}

    @delete("/lexicon/overrides/{wrong_word:str}", status_code=200)
    async def delete_lexicon_override(self, request: Request, wrong_word: str) -> dict:
        """Delete a system-wide STT Override"""
        from backend.services.xohi_memory import xohi_memory
        await xohi_memory.delete_system_stt_override(wrong_word.strip().lower())
        logger.info(f"[Lexicon] Deleted override '{wrong_word}'")
        return {"status": "success", "message": f"Đã xóa luật nắn lỗi cho từ: {wrong_word}"}

    @get("/lexicon/stopwords")
    async def get_lexicon_stopwords(self, request: Request) -> dict:
        """Fetch system-wide Stopwords (Filler words)"""
        from backend.services.xohi_memory import xohi_memory
        stopwords = await xohi_memory.get_system_stt_stopwords()
        return {"stopwords": stopwords}

    @post("/lexicon/stopwords")
    async def add_lexicon_stopword(self, request: Request, data: LexiconStopwordPayload) -> dict:
        """Add a Stopword to the system"""
        from backend.services.xohi_memory import xohi_memory
        word = data.word.strip().lower()
        await xohi_memory.add_system_stt_stopword(word)
        logger.info(f"[Lexicon] Added stopword '{word}'")
        return {"status": "success", "message": f"Đã thêm từ dư thừa: {word}"}

    @delete("/lexicon/stopwords/{word:str}", status_code=200)
    async def delete_lexicon_stopword(self, request: Request, word: str) -> dict:
        """Delete a Stopword from the system"""
        from backend.services.xohi_memory import xohi_memory
        norm_word = word.strip().lower()
        await xohi_memory.delete_system_stt_stopword(norm_word)
        logger.info(f"[Lexicon] Deleted stopword '{word}'")
        return {"status": "success", "message": f"Đã xóa từ dư thừa: {word}"}

