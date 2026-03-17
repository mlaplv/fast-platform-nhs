import uuid
import json
import logging
from typing import Dict, List, Optional, Union
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import HTTPException, NotFoundException

from backend.schemas.voice import (
    VoiceSettingsPayload, VoiceSettingsResponse, CapabilityMetadata,
    CampaignModePayload, LexiconOverridePayload, LexiconStopwordPayload,
    LexiconOverridesResponse, LexiconStopwordsResponse
)
from backend.schemas.common import SuccessResponse
from backend.database.models import User, VoiceProfile
from backend.services.capability_registry import capability_registry
from backend.services.xohi_memory import xohi_memory

logger = logging.getLogger("api-gateway")

class SettingsService:
    @staticmethod
    async def get_voice_settings(db_session: AsyncSession, user_email: str) -> VoiceSettingsResponse:
        """Fetch current voice and cognitive settings (Zero-Hydration). R1.5: Scalar Projection."""
        # R1.5: Scalar Projection Join (Avoiding full ORM hydration for READ)
        stmt = select(
            VoiceProfile.wake_words,
            VoiceProfile.sleep_words,
            VoiceProfile.greeting_template,
            VoiceProfile.farewell_template,
            VoiceProfile.capabilities,
            VoiceProfile.chat_settings,
            VoiceProfile.stt_anchors,
            VoiceProfile.mic_sensitivity
        ).join(User, User.id == VoiceProfile.user_id).where(User.email == user_email)

        result = await db_session.execute(stmt)
        row = result.first()

        if not row:
            # Fallback for new users without profile
            wake, sleep = ["xohi"], ["ngu di"]
            greeting, farewell = "Dạ", "Tạm biệt"
            stored_caps = {}
            chat_settings = {
                "selective_persistence": True, "save_ai_responses": False,
                "auto_purge_days": 30, "cache_limit": 10
            }
            stt_anchors, mic_sensitivity = [], 0.6
        else:
            wake = row.wake_words
            sleep = row.sleep_words
            greeting = row.greeting_template
            farewell = row.farewell_template
            stored_caps = row.capabilities if isinstance(row.capabilities, dict) else json.loads(row.capabilities or "{}")
            chat_settings = row.chat_settings
            stt_anchors = row.stt_anchors or []
            mic_sensitivity = row.mic_sensitivity if row.mic_sensitivity is not None else 0.6

        # Merge Registry Metadata
        capabilities = [
            CapabilityMetadata(**cap, active=stored_caps.get(cap["id"], True))
            for cap in capability_registry.get_spectrum()
        ]

        val = await xohi_memory.client.get("system:campaign_mode")
        is_campaign = val == "1"

        return VoiceSettingsResponse(
            wake_words=wake,
            sleep_words=sleep,
            greeting_template=greeting,
            farewell_template=farewell,
            is_campaign_mode=is_campaign,
            capabilities=capabilities,
            chat_settings=chat_settings,
            stt_anchors=stt_anchors,
            mic_sensitivity=mic_sensitivity
        )

    @staticmethod
    async def update_voice_settings(db_session: AsyncSession, user_email: str, data: VoiceSettingsPayload) -> SuccessResponse:
        """Update user voice identity and cognitive settings (Surgical Update)."""
        # R41: Fetch user first to get ID
        user_stmt = select(User.id).where(User.email == user_email)
        user_id = await db_session.scalar(user_stmt)
        if not user_id:
            raise NotFoundException(detail="User not found")

        # Fetch or Create Profile
        stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_id)
        result = await db_session.execute(stmt)
        profile = result.scalar_one_or_none()

        clean_wake = [w.strip() for w in data.wake_words if w.strip()]
        clean_sleep = [w.strip() for w in data.sleep_words if w.strip()]

        if not profile:
            profile = VoiceProfile(
                id=str(uuid.uuid4()),
                user_id=user_id,
                wake_words=clean_wake,
                sleep_words=clean_sleep,
                greeting_template=data.greeting_template,
                farewell_template=data.farewell_template,
                capabilities=data.capabilities,
                chat_settings=data.chat_settings or {},
                stt_anchors=data.stt_anchors or [],
                mic_sensitivity=data.mic_sensitivity if data.mic_sensitivity is not None else 0.6
            )
            db_session.add(profile)
        else:
            profile.wake_words = clean_wake
            profile.sleep_words = clean_sleep
            profile.greeting_template = data.greeting_template
            profile.farewell_template = data.farewell_template
            profile.capabilities = data.capabilities
            if data.chat_settings is not None:
                profile.chat_settings = data.chat_settings
            if data.stt_anchors is not None:
                profile.stt_anchors = data.stt_anchors
            if data.mic_sensitivity is not None:
                profile.mic_sensitivity = data.mic_sensitivity

        # We don't commit here, Controller handles it as per Rule 13
        # await db_session.flush() # Optional: ensure ID is generated if not set

        # Sync to Redis for real-time engine
        if data.is_campaign_mode is not None:
            await xohi_memory.client.set("system:campaign_mode", "1" if data.is_campaign_mode else "0")

        profile_cache = {
            "wake_words": [w.lower() for w in clean_wake],
            "sleep_words": [w.lower() for w in clean_sleep],
            "greeting_template": profile.greeting_template,
            "farewell_template": profile.farewell_template,
            "capabilities": profile.capabilities,
            "chat_settings": profile.chat_settings,
            "stt_anchors": profile.stt_anchors,
            "mic_sensitivity": profile.mic_sensitivity
        }
        await xohi_memory.cache_voice_profile(user_id, profile_cache)

        # Build response metadata for SuccessResponse data
        capabilities_list = [
            CapabilityMetadata(**cap, active=profile.capabilities.get(cap["id"], True))
            for cap in capability_registry.get_spectrum()
        ]
        val = await xohi_memory.client.get("system:campaign_mode")

        return SuccessResponse(
            ok=True,
            id=str(profile.id),
            message="Đã cập nhật bộ nhận diện giọng nói cho sếp.",
            data=VoiceSettingsResponse(
                wake_words=clean_wake,
                sleep_words=clean_sleep,
                greeting_template=profile.greeting_template,
                farewell_template=profile.farewell_template,
                is_campaign_mode=(val == "1"),
                capabilities=capabilities_list,
                chat_settings=profile.chat_settings,
                stt_anchors=profile.stt_anchors,
                mic_sensitivity=profile.mic_sensitivity
            )
        )

    @staticmethod
    async def toggle_campaign_mode(is_campaign_mode: bool, user_email: str) -> SuccessResponse:
        """Toggle global Campaign Mode state in Redis"""
        val = "1" if is_campaign_mode else "0"
        await xohi_memory.client.set("system:campaign_mode", val)

        status_msg = "BẬT" if is_campaign_mode else "TẮT"
        logger.info(f"[Settings] User {user_email} toggled Campaign Mode: {is_campaign_mode}")

        return SuccessResponse(
            ok=True,
            message=f"Đã {status_msg} chế độ Chiến Dịch Quảng Cáo."
        )

    @staticmethod
    async def get_campaign_mode() -> CampaignModeResponse:
        """Fetch global Campaign Mode state from Redis"""
        val = await xohi_memory.client.get("system:campaign_mode")
        is_campaign = val == "1"
        return CampaignModeResponse(is_campaign_mode=is_campaign)

    @staticmethod
    async def get_lexicon_overrides() -> LexiconOverridesResponse:
        overrides = await xohi_memory.get_system_stt_overrides()
        return LexiconOverridesResponse(overrides=overrides)

    @staticmethod
    async def add_lexicon_override(data: LexiconOverridePayload) -> SuccessResponse:
        mapping = {data.wrong_word.strip().lower(): data.right_word.strip()}
        await xohi_memory.set_system_stt_overrides(mapping)
        logger.info(f"[Lexicon] Added override '{data.wrong_word}' -> '{data.right_word}'")
        return SuccessResponse(ok=True, message=f"Đã thêm luật nắn lỗi: {data.wrong_word} ➔ {data.right_word}")

    @staticmethod
    async def delete_lexicon_override(wrong_word: str) -> SuccessResponse:
        await xohi_memory.delete_system_stt_override(wrong_word.strip().lower())
        logger.info(f"[Lexicon] Deleted override '{wrong_word}'")
        return SuccessResponse(ok=True, message=f"Đã xóa luật nắn lỗi cho từ: {wrong_word}")

    @staticmethod
    async def get_lexicon_stopwords() -> LexiconStopwordsResponse:
        stopwords = await xohi_memory.get_system_stt_stopwords()
        return LexiconStopwordsResponse(stopwords=stopwords)

    @staticmethod
    async def add_lexicon_stopword(word: str) -> SuccessResponse:
        word = word.strip().lower()
        await xohi_memory.add_system_stt_stopword(word)
        logger.info(f"[Lexicon] Added stopword '{word}'")
        return SuccessResponse(ok=True, message=f"Đã thêm từ dư thừa: {word}")

    @staticmethod
    async def delete_lexicon_stopword(word: str) -> SuccessResponse:
        norm_word = word.strip().lower()
        await xohi_memory.delete_system_stt_stopword(norm_word)
        logger.info(f"[Lexicon] Deleted stopword '{word}'")
        return SuccessResponse(ok=True, message=f"Đã xóa từ dư thừa: {word}")

settings_service = SettingsService()
