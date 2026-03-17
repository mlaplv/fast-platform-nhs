import io
import os
import re
import logging
import asyncio
import unicodedata
import uuid
import httpx
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING, cast, TypedDict
from sqlalchemy import select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

import litellm
import edge_tts
from backend.services.xohi_memory import xohi_memory
from backend.services.stt_corrector import stt_corrector
from backend.services.ai_engine.key_rotator import key_rotator
from backend.utils.security import GeminiSecurity

if TYPE_CHECKING:
    from litellm.utils import TranscriptionResponse

class WhisperSegment(TypedDict):
    """LiteLLM Whisper Segment structure."""
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float

logger = logging.getLogger("api-gateway")

# Constants from legacy voice_stream
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WHISPER_MODEL = "groq/whisper-large-v3-turbo"
MIN_AUDIO_BYTES = 1500

HALLUCINATION_BLACKLIST = [
    "cám ơn các bạn", "subscribe", "đăng ký kênh", "ghiền mì gõ",
    "chào các bạn", "phimmoichill", "website chính thức",
    "liên hệ với chúng tôi", "video", "youtube", "mọi người",
    "ủng hộ", "bình luận", "zalo", "facebook", "website", "chào mừng",
    "tập trung vào ngữ cảnh"
]

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')
DOT_HALLUCINATION_RE = re.compile(r'^\.+$')

class VoiceService:
    """
    ULTRA-LEAN VOICE SERVICE (ELITE V2.2)
    ------------------------------------
    Centralizes STT, Transcription, AI Profile and Model Management.
    Zero-Hydration (Rule 1.5): Raw SQL & Scalar Projection for <2GB RAM.
    """

    async def transcribe_and_correct(
        self,
        audio_data: bytes,
        user_id: Optional[str] = None,
        is_partial: bool = False
    ) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        Full pipeline: Audio -> Whisper -> Deduplication -> Hallucination Filter -> STT Corrector.
        """
        if len(audio_data) < MIN_AUDIO_BYTES:
            return "", None

        raw_transcript = await self._raw_transcribe(audio_data, user_id)
        if not raw_transcript:
            return "", None

        filtered_text = self._filter_transcript(raw_transcript)
        if not filtered_text:
            return "", None

        if is_partial:
            return filtered_text, None

        user_dict = {}
        if user_id:
            user_dict = await xohi_memory.get_stt_dictionary(user_id)

        corrected_text, suspected = await stt_corrector.correct(filtered_text, user_dictionary=user_dict)
        return corrected_text, suspected

    async def _get_or_create_profile(self, session: AsyncSession, user_id: str) -> str:
        """Internal helper to ensure profile exists and return its ID (Zero-Hydration)."""
        sql = text("SELECT id FROM voice_profiles WHERE user_id = :uid")
        pid = await session.scalar(sql, {"uid": user_id})

        if not pid:
            pid = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO voice_profiles (id, user_id, created_at, updated_at)
                    VALUES (:id, :uid, NOW(), NOW())
                """),
                {"id": pid, "uid": user_id}
            )
            # No commit here, let the caller decide
        return str(pid)

    async def update_gemini_keys(self, session: AsyncSession, user_id: str, keys: List[str]) -> int:
        """Encrypt and save a new pool of Gemini keys via direct SQL."""
        if not keys:
            return 0

        encrypted_blob = GeminiSecurity.encrypt_keys(keys)
        await self._get_or_create_profile(session, user_id)

        await session.execute(
            text("UPDATE voice_profiles SET gemini_keys_enc = :enc, updated_at = NOW() WHERE user_id = :uid"),
            {"enc": encrypted_blob, "uid": user_id}
        )

        await session.commit()
        await key_rotator.load_keys()
        return len(keys)

    async def discover_models(self, session: AsyncSession, user_id: str) -> List[str]:
        """Fetch available Gemini models and persist to profile via direct SQL."""
        key = await key_rotator.get_key()
        models: List[str] = []

        if key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("models", []):
                        name = m.get("name", "").replace("models/", "")
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods and "gemini" in name:
                            models.append(name)
                    models.sort()

        if models:
            await self._get_or_create_profile(session, user_id)
            import json
            await session.execute(
                text("UPDATE voice_profiles SET discovered_models = :models, updated_at = NOW() WHERE user_id = :uid"),
                {"models": json.dumps(models), "uid": user_id}
            )
            await session.commit()

        return models

    async def update_model_config(
        self,
        session: AsyncSession,
        user_id: str,
        primary_model: Optional[str],
        waterfall: List[str]
    ) -> None:
        """Update AI model configuration via direct SQL and hot-reload TrinityBridge."""
        await self._get_or_create_profile(session, user_id)
        import json
        await session.execute(
            text("""
                UPDATE voice_profiles
                SET primary_model = :pm, ai_models = :waterfall, updated_at = NOW()
                WHERE user_id = :uid
            """),
            {"pm": primary_model, "waterfall": json.dumps(waterfall), "uid": user_id}
        )

        await session.commit()

        from backend.services.ai_engine.trinity_bridge import trinity_bridge
        trinity_bridge.db_primary_model = primary_model
        trinity_bridge.db_waterfall = waterfall
        logger.info(f"[VoiceService] TrinityBridge hot-reloaded for user {user_id}")

    async def get_key_stats(self) -> List[Dict[str, object]]:
        """Fetch real-time metrics for all Gemini keys via key_rotator."""
        import time
        all_keys = key_rotator.keys
        stats = []
        now = time.time()

        for idx, key in enumerate(all_keys):
            kid = key_rotator._get_key_id(key)
            if key_rotator._use_redis and key_rotator.client:
                meta = await key_rotator.client.hgetall(f"{key_rotator.METADATA_PREFIX}{kid}")
                is_blacklisted = await key_rotator.client.exists(f"{key_rotator.BLACKLIST_PREFIX}{kid}")
            else:
                meta = {}
                is_blacklisted = False

            fail_count = int(meta.get("fail_count", 0))
            last_used = float(meta.get("last_used", 0))

            status = "ACTIVE"
            if is_blacklisted:
                status = "DEAD"
            elif fail_count > 0:
                cooldown = min(key_rotator.BASE_COOLDOWN * (2 ** (fail_count - 1)), key_rotator.MAX_COOLDOWN)
                if now - last_used < cooldown:
                    status = "COOLDOWN"

            stats.append({
                "index": idx,
                "key_preview": f"{key[:8]}...{key[-4:]}",
                "fail_count": fail_count,
                "health_score": int(meta.get("health_score", 100)),
                "status": status,
                "last_used": last_used
            })
        return stats

    async def test_key(self, index: int) -> Dict[str, str]:
        """Manually trigger a health check for a specific key."""
        if index < 0 or index >= len(key_rotator.keys):
            return {"status": "error", "message": "Invalid index"}

        key = key_rotator.keys[index]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
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

    def _merge_capabilities(self, stored_caps: Dict[str, bool]) -> List[Dict[str, object]]:
        """Helper to merge registry metadata with user's active state."""
        from backend.services.capability_registry import capability_registry
        capabilities = []
        for cap in capability_registry.get_spectrum():
            capabilities.append({
                **cap,
                "active": stored_caps.get(cap["id"], True)
            })
        return capabilities

    async def get_voice_settings(self, session: AsyncSession, user_id: str) -> Dict[str, object]:
        """Fetch current voice and cognitive settings for a user via text-SQL (Zero-Hydration)."""
        from backend.services.xohi_memory import xohi_memory
        import json

        sql = text("""
            SELECT wake_words, sleep_words, greeting_template, farewell_template, capabilities, chat_settings
            FROM voice_profiles
            WHERE user_id = :uid
        """)
        res = await session.execute(sql, {"uid": user_id})
        r = res.first()

        def _parse_json(val, default):
            if not val: return default
            if isinstance(val, (list, dict)): return val
            try: return json.loads(val)
            except: return default

        if not r:
            wake_words, sleep_words = ["xohi"], ["ngu di"]
            greeting, farewell = "Dạ", "Tạm biệt"
            stored_caps = {}
            chat_settings = {
                "selective_persistence": True,
                "save_ai_responses": False,
                "auto_purge_days": 30,
                "cache_limit": 10
            }
        else:
            wake_words = _parse_json(r[0], ["xohi"])
            sleep_words = _parse_json(r[1], ["ngu di"])
            greeting = r[2] or "Dạ"
            farewell = r[3] or "Tạm biệt"
            stored_caps = _parse_json(r[4], {})
            chat_settings = _parse_json(r[5], {
                "selective_persistence": True,
                "save_ai_responses": False,
                "auto_purge_days": 30,
                "cache_limit": 10
            })

        # Merge Registry Metadata with User's Active State
        capabilities = self._merge_capabilities(stored_caps)

        # Global Campaign Mode from Redis
        val = await xohi_memory.client.get("system:campaign_mode")
        is_campaign = val == "1"

        return {
            "wake_words": wake_words,
            "sleep_words": sleep_words,
            "greeting_template": greeting,
            "farewell_template": farewell,
            "is_campaign_mode": is_campaign,
            "capabilities": capabilities,
            "chat_settings": chat_settings
        }

    async def update_profile(self, session: AsyncSession, user_id: str, data: Dict[str, object]) -> Dict[str, object]:
        """Update or create a voice profile via direct SQL (Zero-Hydration)."""
        await self._get_or_create_profile(session, user_id)

        import json
        set_clauses = []
        params = {"uid": user_id}

        mapping = {
            "wake_words": "wake_words",
            "sleep_words": "sleep_words",
            "greeting_template": "greeting_template",
            "farewell_template": "farewell_template",
            "capabilities": "capabilities",
            "chat_settings": "chat_settings",
            "primary_model": "primary_model",
            "ai_models": "ai_models"
        }

        for key, db_col in mapping.items():
            if key in data:
                set_clauses.append(f"{db_col} = :{key}")
                val = data[key]
                params[key] = json.dumps(val) if isinstance(val, (list, dict)) else val

        if not set_clauses:
            return {"user_id": user_id, "message": "No changes"}

        set_clauses.append("updated_at = NOW()")
        sql = text(f"UPDATE voice_profiles SET {', '.join(set_clauses)} WHERE user_id = :uid RETURNING id, wake_words, primary_model, greeting_template, farewell_template, capabilities, chat_settings")
        res = await session.execute(sql, params)
        r = res.first()

        await session.commit()

        def _parse(v):
            if isinstance(v, str):
                try: return json.loads(v)
                except: return v
            return v

        return {
            "id": str(r[0]) if r else None,
            "user_id": user_id,
            "wake_words": _parse(r[1]) if r else [],
            "primary_model": r[2] if r else None,
            "greeting_template": r[3] if r else "Dạ",
            "farewell_template": r[4] if r else "Tạm biệt",
            "capabilities": _parse(r[5]) if r else {},
            "chat_settings": _parse(r[6]) if r else {}
        }

    async def get_model_config(self, session: AsyncSession, user_id: str) -> Dict[str, object]:
        """Fetch current AI model configuration with defaults via text-SQL."""
        from backend.services.ai_engine.trinity_bridge import trinity_bridge
        import json

        sql = text("SELECT primary_model, ai_models, discovered_models FROM voice_profiles WHERE user_id = :uid")
        res = await session.execute(sql, {"uid": user_id})
        r = res.first()

        if not r:
            return {
                "primary_model": trinity_bridge.default_model_name,
                "ai_models": trinity_bridge.model_waterfall,
                "discovered_models": []
            }

        def _parse(v, default):
            if not v: return default
            if isinstance(v, (list, dict)): return v
            try: return json.loads(v)
            except: return default

        return {
            "primary_model": r[0] or trinity_bridge.default_model_name,
            "ai_models": _parse(r[1], trinity_bridge.model_waterfall),
            "discovered_models": _parse(r[2], [])
        }

    async def reset_health(self) -> Dict[str, object]:
        """Reset all key health states via key_rotator."""
        if not key_rotator._use_redis or not key_rotator.client:
            return {"status": "error", "message": "Redis unavailable"}

        cleared = await key_rotator.reset_health()
        return {"status": "success", "cleared": cleared, "message": "Đã reset hệ thống Key và nạp lại từ DB."}

    async def update_voice_settings(
        self,
        session: AsyncSession,
        user_id: str,
        data: Dict[str, object]
    ) -> Dict[str, object]:
        """
        [MẶT TRẬN 4] - Unified Update for Voice Identity and Cognitive Capabilities.
        Handles cleaning, DB persistence, and Redis hot-reload.
        """
        # 1. Clean words
        def smart_dedup(words: List[str]) -> List[str]:
            seen = set()
            res = []
            for w in words:
                w_strip = w.strip()
                if not w_strip: continue
                w_norm = w_strip.lower()
                if w_norm not in seen:
                    seen.add(w_norm)
                    res.append(w_strip)
            return res

        wake_words = smart_dedup(cast(List[str], data.get("wake_words", [])))
        sleep_words = smart_dedup(cast(List[str], data.get("sleep_words", [])))

        # 2. Update DB Profile
        profile_update = {
            "wake_words": wake_words,
            "sleep_words": sleep_words,
            "greeting_template": data.get("greeting_template"),
            "farewell_template": data.get("farewell_template"),
            "capabilities": data.get("capabilities"),
            "chat_settings": data.get("chat_settings")
        }
        profile = await self.update_profile(session, user_id, {k: v for k, v in profile_update.items() if v is not None})

        # 3. Hot Reload to Redis
        redis_data = {
            "wake_words":        [w.lower() for w in wake_words],
            "sleep_words":       [w.lower() for w in sleep_words],
            "greeting_template": profile["greeting_template"],
            "farewell_template": profile["farewell_template"],
            "capabilities":      profile["capabilities"],
            "chat_settings":     profile["chat_settings"],
        }

        # Global Campaign Mode
        is_campaign_mode = data.get("is_campaign_mode")
        if is_campaign_mode is not None:
            val = "1" if is_campaign_mode else "0"
            await xohi_memory.client.set("system:campaign_mode", val)

        await xohi_memory.cache_voice_profile(user_id, redis_data)

        # 4. Return summary
        val = await xohi_memory.client.get("system:campaign_mode")
        current_campaign = val == "1"

        return {
            "wake_words": wake_words,
            "sleep_words": sleep_words,
            "greeting_template": profile["greeting_template"],
            "farewell_template": profile["farewell_template"],
            "capabilities": self._merge_capabilities(profile["capabilities"]),
            "chat_settings": profile["chat_settings"],
            "is_campaign_mode": current_campaign
        }

    async def _raw_transcribe(self, audio_data: bytes, user_id: Optional[str] = None) -> str:
        """Internal Whisper call via litellm."""
        try:
            audio_file = io.BytesIO(audio_data)
            ext = "webm"
            if audio_data.startswith(b'\x1aE\xdf\xa3'): ext = "webm"
            elif audio_data.startswith(b'OggS'): ext = "ogg"
            elif b'ftyp' in audio_data[:32]: ext = "mp4"
            audio_file.name = f"audio.{ext}"

            stt_anchors = []
            mic_sensitivity = 0.6
            if user_id:
                profile_data = await xohi_memory.get_voice_profile(user_id)
                if profile_data:
                    stt_anchors = profile_data.get("stt_anchors", [])
                    mic_sensitivity = profile_data.get("mic_sensitivity", 0.6)

            system_mapping = await xohi_memory.get_system_intent_mapping()
            system_intents = list(system_mapping.keys())[:10] if system_mapping else []
            final_anchors = " ".join(stt_anchors + system_intents)
            prompt_text = final_anchors[:500]

            response: "TranscriptionResponse" = await litellm.atranscription(
                model=WHISPER_MODEL,
                file=audio_file,
                language="vi",
                api_key=GROQ_API_KEY,
                prompt=prompt_text,
                temperature=0.0,
                response_format="verbose_json"
            )

            raw_text = getattr(response, "text", "")
            if not isinstance(raw_text, str):
                return ""

            transcript = unicodedata.normalize('NFC', raw_text.strip())

            kill_switch_triggered = False
            segments: List[WhisperSegment] = []

            if hasattr(response, "segments") and response.segments:
                segments = cast(List[WhisperSegment], response.segments)
            elif isinstance(response, dict) and "segments" in response:
                segments = cast(List[WhisperSegment], response["segments"])

            for seg in segments:
                no_speech = float(seg.get("no_speech_prob", 0.0))
                comp_ratio = float(seg.get("compression_ratio", 0.0))
                if no_speech > mic_sensitivity or comp_ratio > 2.4:
                    logger.warning(f"[VoiceService] Kill-Switch! no_speech={no_speech:.2f}, comp_ratio={comp_ratio:.2f}")
                    kill_switch_triggered = True
                    break

            if kill_switch_triggered:
                return ""

            return transcript

        except Exception as e:
            logger.error(f"[VoiceService] Transcription failed: {e}")
            return ""

    def _filter_transcript(self, transcript: str) -> str:
        """Deduplication and Hallucination Filtering."""
        if not transcript:
            return ""

        parts = [p.strip() for p in SENTENCE_SPLIT_RE.split(transcript) if p.strip()]
        unique_parts: List[str] = []

        for p in parts:
            p_lower = p.lower()
            if DOT_HALLUCINATION_RE.match(p_lower):
                continue

            if not unique_parts:
                unique_parts.append(p)
            else:
                last = unique_parts[-1].lower()
                if p_lower in last:
                    continue
                elif last in p_lower:
                    unique_parts[-1] = p
                else:
                    unique_parts.append(p)

        clean_parts = []
        for p in unique_parts:
            p_lower = p.lower()
            if not any(bad in p_lower for bad in HALLUCINATION_BLACKLIST):
                clean_parts.append(p)
            else:
                logger.warning(f"[VoiceService] Hallucination stripped: '{p}'")

        return " ".join(clean_parts)

    async def stream_tts(self, text: str):
        """
        Module 1: THE LUNGS (BACKEND EDGE-TTS STREAMING)
        Generates audio chunks via edge-tts and yields them immediately.
        Hợp nhất từ tts_engine (Elite V2.2).
        """
        communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural")
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        except GeneratorExit:
            logger.info("[TTS] Client disconnected — stream aborted gracefully")
        finally:
            logger.debug("[TTS] Stream cleanup complete")

# Singleton
voice_service = VoiceService()
