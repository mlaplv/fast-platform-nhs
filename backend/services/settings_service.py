import uuid
import json
import logging
from typing import Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import NotFoundException

from backend.schemas.voice import (
    VoiceSettingsPayload, VoiceSettingsResponse, CapabilityMetadata,
    CampaignModeResponse,
    LexiconOverridePayload,
    LexiconOverridesResponse, LexiconStopwordsResponse
)
from backend.schemas.system_settings import SystemSettingsPayload, SystemSettingsResponse
from backend.schemas.common import SuccessResponse
from backend.database.models import User, VoiceProfile, SystemSetting
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
    async def get_lexicon_stopword(word: str) -> LexiconStopwordsResponse:
        stopwords = await xohi_memory.get_system_stt_stopwords()
        return LexiconStopwordsResponse(stopwords=stopwords)

    @staticmethod
    async def get_general_settings(db_session: AsyncSession) -> SystemSettingsResponse:
        """Fetch global system settings with Redis cache (Elite V2.2)."""
        # 1. Try cache first
        cached = await xohi_memory.client.get("system:settings:primary_config")
        if cached:
            return SystemSettingsResponse(settings=SystemSettingsPayload(**json.loads(cached)))

        # 2. Fallback to DB
        stmt = select(SystemSetting).where(SystemSetting.key == "primary_config")
        result = await db_session.execute(stmt)
        setting = result.scalar_one_or_none()

        if not setting:
            return SystemSettingsResponse(settings=SystemSettingsPayload())

        # 3. Update cache
        await xohi_memory.client.set("system:settings:primary_config", json.dumps(setting.value))

        return SystemSettingsResponse(settings=SystemSettingsPayload(**setting.value))

    @staticmethod
    async def update_general_settings(db_session: AsyncSession, data: SystemSettingsPayload) -> SuccessResponse:
        """Update global system settings and invalidate cache."""
        stmt = select(SystemSetting).where(SystemSetting.key == "primary_config")
        result = await db_session.execute(stmt)
        setting = result.scalar_one_or_none()

        data_dict = data.model_dump()

        if not setting:
            setting = SystemSetting(
                key="primary_config",
                value=data_dict
            )
            db_session.add(setting)
        else:
            setting.value = data_dict

        # Invalidate cache
        await xohi_memory.client.delete("system:settings:primary_config")

        # Cache important values in Redis (e.g., maintenance mode, helen bot)
        await xohi_memory.client.set("system:maintenance_mode", "1" if data.maintenance.is_enabled else "0")
        await xohi_memory.client.set("system:helen_enabled", "1" if data.support_bot.helen_enabled else "0")
        await xohi_memory.client.set("system:helen_offline_msg", data.support_bot.offline_message)
        await xohi_memory.client.set("system:zalo_enabled", "1" if data.support_bot.zalo_integration_enabled else "0")
        await xohi_memory.client.set("system:messenger_enabled", "1" if data.support_bot.messenger_integration_enabled else "0")
        await xohi_memory.client.set("system:fomo_enabled", "1" if data.conversions.fomo_enabled else "0")
        
        # Cache Autopilot settings in Redis
        await xohi_memory.client.set("system:autopilot:scan_start_hour", str(data.autopilot.scan_start_hour))
        await xohi_memory.client.set("system:autopilot:scan_end_hour", str(data.autopilot.scan_end_hour))
        
        # Elite V2.2: Sync Currency
        await xohi_memory.client.set("system:currency:symbol", data.currency.symbol)
        await xohi_memory.client.set("system:currency:position", data.currency.position)
        await xohi_memory.client.set("system:currency:thousand_sep", data.currency.thousand_separator)
        await xohi_memory.client.set("system:currency:decimal_sep", data.currency.decimal_separator)

        # SGE Shield V1.0: Sync Entropy Settings vào Redis + in-process cache
        import json as _json
        from backend.services.commerce.seo_service import update_entropy_cache
        entropy_dict = data.entropy.model_dump()
        await xohi_memory.client.set(
            "system:entropy_config",
            _json.dumps(entropy_dict),
        )
        update_entropy_cache(entropy_dict)

        # Sync News Tags mapping to Redis
        news_tags_dict = data.news_tags.tags_map
        await xohi_memory.client.set(
            "system:news_tags",
            _json.dumps(news_tags_dict),
        )

        # Elite V2.2: Sync Media
        await SettingsService._sync_media_links(data_dict)

        return SuccessResponse(
            ok=True,
            message="Đã cập nhật cấu hình hệ thống.",
            data=SystemSettingsResponse(settings=data).model_dump()
        )

    @staticmethod
    async def _sync_media_links(settings_dict: Dict) -> None:
        """Đồng bộ Media cho cấu hình hệ thống (Recursive Scan)."""
        try:
            from backend.utils.media import extract_media_urls
            from backend.services.event_bus import event_bus
            urls = extract_media_urls(settings_dict)
            if urls:
                await event_bus.emit("MEDIA_SYNC_REQUIRED", {
                    "entity_id": "primary_config",
                    "entity_type": "system_settings",
                    "urls": list(urls)
                })
                logger.info(f"[SettingsService] Emitted MEDIA_SYNC_REQUIRED for system settings with {len(urls)} URLs")
        except Exception as e:
            logger.error(f"[SettingsService] Failed to emit media sync: {e}")

settings_service = SettingsService()
async def provide_settings_service() -> SettingsService:
    """Standard Litestar Provider for SettingsService."""
    return settings_service
