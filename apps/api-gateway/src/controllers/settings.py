import logging
import json
import os
import uuid
from typing import Dict, List, Optional, Union
from litestar import Controller, post, get, Request
from litestar.di import Provide
from litestar.exceptions import HTTPException
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from src.schemas.voice import VoiceSettingsPayload, VoiceSettingsResponse, CapabilityMetadata
from src.database.models import User, VoiceProfile
from src.database.repositories import UserRepository, VoiceProfileRepository, provide_user_repo, provide_voice_repo
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

    @get("/voice")
    async def get_voice_settings(self, user_repo: UserRepository, request: Request) -> VoiceSettingsResponse:
        """Fetch current voice and cognitive settings (Dynamic Matrix)"""
        user_info = getattr(request.state, "user", None)
        if not user_info or "sub" not in user_info:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Use direct SQLAlchemy with selectinload (Rule R41)
        stmt = select(User).where(User.email == user_info["sub"]).options(
            selectinload(User.voice_profile)
        )
        res = await user_repo.session.execute(stmt)
        user = res.scalar_one_or_none()
        
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
        greeting = profile.greeting_template if profile else "Dạ, em nghe đây sếp."
        
        return VoiceSettingsResponse(
            wake_words=wake,
            sleep_words=sleep,
            greeting_template=greeting,
            capabilities=capabilities
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

        # Use direct SQLAlchemy with selectinload (Rule R41)
        stmt = select(User).where(User.email == user_info["sub"]).options(
            selectinload(User.voice_profile)
        )
        res = await user_repo.session.execute(stmt)
        user = res.scalar_one_or_none()
        
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
                capabilities=data.capabilities
            )
            await voice_repo.add(profile)
        else:
            profile.wake_words = clean_wake
            profile.sleep_words = clean_sleep
            profile.greeting_template = data.greeting_template
            profile.capabilities = data.capabilities

        await voice_repo.session.commit()

        # HOT RELOAD TO REDIS
        from src.services.xohi_memory import xohi_memory
        
        profile_data = {
            "wake_words":        [normalize_vn(w) for w in clean_wake],
            "sleep_words":       [normalize_vn(w) for w in clean_sleep],
            "greeting_template": data.greeting_template,
            "capabilities":      data.capabilities,
        }
        await xohi_memory.cache_voice_profile(user_id, profile_data)

        return {
            "status": "success",
            "message": "Đã cập nhật bộ nhận diện giọng nói cho sếp.",
            "data": {
                "wake_words": clean_wake,
                "sleep_words": clean_sleep,
                "greeting_template": data.greeting_template,
                "capabilities": data.capabilities
            }
        }
