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

from src.schemas.voice import (
    VoiceSettingsPayload, VoiceSettingsResponse, CapabilityMetadata, 
    CampaignModePayload, LexiconOverridePayload, LexiconStopwordPayload
)
from src.database.models import User, VoiceProfile
from src.database.repositories import UserRepository, VoiceProfileRepository, provide_user_repo, provide_voice_repo
from src.constants.voice import DEFAULT_GREETING, DEFAULT_FAREWELL
from src.utils.text import normalize_vn
from src.services.capability_registry import capability_registry
from src.guards import PermissionGuard


logger = logging.getLogger("api-gateway")


class SettingsController(Controller):
    """
    R2 (V30.0): Strict Class-based Controller for Administrative Settings.
    Manages per-user configurations for Voice Identity and Cognitive Capabilities.
    """
    path = "/api/v1/settings"
    guards = [PermissionGuard("system:all")]
    dependencies = {
        "user_repo": Provide(provide_user_repo),
        "voice_repo": Provide(provide_voice_repo),
    }

    async def _get_user_with_profile(self, user_repo: UserRepository, email: str) -> Optional[User]:
        """Core helper to fetch user with voice profile (N+1 Optimized)"""
        stmt = select(User).where(User.email == email).options(selectinload(User.voice_profile))
        result = await user_repo.session.execute(stmt)
        return result.scalar_one_or_none()

    @get("/voice")
    async def get_voice_settings(self, user_repo: UserRepository, request: Request) -> VoiceSettingsResponse:
        """Fetch current voice and cognitive settings (Dynamic Matrix)"""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user = await self._get_user_with_profile(user_repo, user_info["sub"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile = user.voice_profile
        stored_caps = {}
        if profile and profile.capabilities:
            stored_caps = profile.capabilities if isinstance(profile.capabilities, dict) else json.loads(profile.capabilities)

        # Merge Registry Metadata with User's Active State
        capabilities = []
        for cap in capability_registry.get_spectrum():
            # Override 'active' from database, keep metadata from registry
            capabilities.append(CapabilityMetadata(
                **cap,
                active=stored_caps.get(cap["id"], True)
            ))

        wake = profile.wake_words if profile else ["xohi"]
        sleep = profile.sleep_words if profile else ["ngu di"]
        greeting = profile.greeting_template if profile else "Dạ"
        farewell = profile.farewell_template if profile else "Tạm biệt"
        
        # [XOHI] Campaign Mode is global in Redis, not in DB Profile
        from src.services.xohi_memory import xohi_memory
        val = await xohi_memory.client.get("system:campaign_mode")
        is_campaign = val == "1"
        
        # Consistent fallbacks for chat_settings
        default_chat = {
            "selective_persistence": True,
            "save_ai_responses": False,
            "auto_purge_days": 30,
            "cache_limit": 10
        }
        chat_settings = profile.chat_settings if profile and profile.chat_settings else default_chat

        return VoiceSettingsResponse(
            wake_words=wake,
            sleep_words=sleep,
            greeting_template=greeting,
            farewell_template=farewell,
            is_campaign_mode=is_campaign,
            capabilities=capabilities,
            chat_settings=chat_settings
        )

    @post("/voice")
    async def update_voice_settings(
        self, user_repo: UserRepository, voice_repo: VoiceProfileRepository, request: Request, data: VoiceSettingsPayload
    ) -> dict:
        """
        [MẶT TRẬN 4] - Dynamic Per-User Setup using repositories
        """
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user = await self._get_user_with_profile(user_repo, user_info["sub"])
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user.id)

        # Helper to dedup based on normalized text
        def smart_dedup(words):
            seen = set()
            res = []
            for w in words:
                w_strip = w.strip()
                if not w_strip: continue
                w_norm = normalize_vn(w_strip)
                if w_norm not in seen:
                    seen.add(w_norm)
                    res.append(w_strip)
            return res

        clean_wake = smart_dedup(data.wake_words)
        clean_sleep = smart_dedup(data.sleep_words)

        # Upsert logic via repository
        profile = user.voice_profile
        if not profile:
            profile = VoiceProfile(
                id=str(uuid.uuid4()),
                user_id=user_id,
                wake_words=clean_wake,
                sleep_words=clean_sleep,
                greeting_template=data.greeting_template,
                farewell_template=data.farewell_template,
                capabilities=data.capabilities,
                chat_settings=data.chat_settings
            )
            await voice_repo.add(profile)
        else:
            profile.wake_words = clean_wake
            profile.sleep_words = clean_sleep
            profile.greeting_template = data.greeting_template
            profile.farewell_template = data.farewell_template
            profile.capabilities = data.capabilities
            if data.chat_settings is not None:
                profile.chat_settings = data.chat_settings

        profile_data = {
            "wake_words":        [normalize_vn(w) for w in clean_wake],
            "sleep_words":       [normalize_vn(w) for w in clean_sleep],
            "greeting_template": data.greeting_template,
            "farewell_template": data.farewell_template,
            "capabilities":      data.capabilities,
            "chat_settings":     profile.chat_settings,
        }

        await voice_repo.session.commit()

        # HOT RELOAD TO REDIS
        from src.services.xohi_memory import xohi_memory
        
        # Unified: Update global campaign mode if provided
        if data.is_campaign_mode is not None:
            val = "1" if data.is_campaign_mode else "0"
            await xohi_memory.client.set("system:campaign_mode", val)
            logger.info(f"[Settings] Unified commit: Campaign Mode set to {data.is_campaign_mode}")

        await xohi_memory.cache_voice_profile(user_id, profile_data)

        # Re-fetch campaign mode to ensure sync
        val = await xohi_memory.client.get("system:campaign_mode")
        current_campaign = val == "1"

        return {
            "status": "success",
            "message": "Đã cập nhật bộ nhận diện giọng nói cho sếp.",
            "data": {
                "wake_words": clean_wake,
                "sleep_words": clean_sleep,
                "greeting_template": data.greeting_template,
                "farewell_template": data.farewell_template,
                "capabilities": data.capabilities,
                "is_campaign_mode": current_campaign
            }
        }

    @get("/campaign-mode", dependencies={})
    async def get_campaign_mode(self, request: Request) -> dict:
        """Fetch global Campaign Mode state from Redis"""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        from src.services.xohi_memory import xohi_memory
        val = await xohi_memory.client.get("system:campaign_mode")
        is_campaign = val == "1"
        return {"is_campaign_mode": is_campaign}

    @post("/campaign-mode", dependencies={})
    async def toggle_campaign_mode(self, request: Request, data: CampaignModePayload) -> dict:
        """Toggle global Campaign Mode state in Redis"""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")
            
        from src.services.xohi_memory import xohi_memory
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
        from src.services.xohi_memory import xohi_memory
        overrides = await xohi_memory.get_system_stt_overrides()
        return {"overrides": overrides}

    @post("/lexicon/overrides")
    async def add_lexicon_override(self, request: Request, data: LexiconOverridePayload) -> dict:
        """Add or update a system-wide STT Override"""
        from src.services.xohi_memory import xohi_memory
        mapping = {normalize_vn(data.wrong_word.strip()): data.right_word.strip()}
        await xohi_memory.set_system_stt_overrides(mapping)
        logger.info(f"[Lexicon] Added override '{data.wrong_word}' -> '{data.right_word}'")
        return {"status": "success", "message": f"Đã thêm luật nắn lỗi: {data.wrong_word} ➔ {data.right_word}"}

    @delete("/lexicon/overrides/{wrong_word:str}", status_code=200)
    async def delete_lexicon_override(self, request: Request, wrong_word: str) -> dict:
        """Delete a system-wide STT Override"""
        from src.services.xohi_memory import xohi_memory
        await xohi_memory.delete_system_stt_override(normalize_vn(wrong_word.strip()))
        logger.info(f"[Lexicon] Deleted override '{wrong_word}'")
        return {"status": "success", "message": f"Đã xóa luật nắn lỗi cho từ: {wrong_word}"}

    @get("/lexicon/stopwords")
    async def get_lexicon_stopwords(self, request: Request) -> dict:
        """Fetch system-wide Stopwords (Filler words)"""
        from src.services.xohi_memory import xohi_memory
        stopwords = await xohi_memory.get_system_stt_stopwords()
        return {"stopwords": stopwords}

    @post("/lexicon/stopwords")
    async def add_lexicon_stopword(self, request: Request, data: LexiconStopwordPayload) -> dict:
        """Add a Stopword to the system"""
        from src.services.xohi_memory import xohi_memory
        word = normalize_vn(data.word.strip())
        await xohi_memory.add_system_stt_stopword(word)
        logger.info(f"[Lexicon] Added stopword '{word}'")
        return {"status": "success", "message": f"Đã thêm từ dư thừa: {word}"}

    @delete("/lexicon/stopwords/{word:str}", status_code=200)
    async def delete_lexicon_stopword(self, request: Request, word: str) -> dict:
        """Delete a Stopword from the system"""
        from src.services.xohi_memory import xohi_memory
        norm_word = normalize_vn(word.strip())
        await xohi_memory.delete_system_stt_stopword(norm_word)
        logger.info(f"[Lexicon] Deleted stopword '{word}'")
        return {"status": "success", "message": f"Đã xóa từ dư thừa: {word}"}

