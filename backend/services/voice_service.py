import io
import os
import re
import logging
import asyncio
import unicodedata
import uuid
import httpx
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING, cast, TypedDict
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import litellm
from backend.database.models import VoiceProfile
from backend.services.xohi_memory import xohi_memory
from backend.services.routing.stt_corrector import stt_corrector
from backend.services.ai_engine.core.key_rotator import key_rotator
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

    async def get_or_create_profile(self, session: AsyncSession, user_id: str) -> VoiceProfile:
        """Fetch or initialize a VoiceProfile for a user."""
        stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_id)
            session.add(profile)
            await session.flush() # Ensure ID is generated

        return profile

    async def update_gemini_keys(self, session: AsyncSession, user_id: str, keys: List[str]) -> int:
        """Encrypt and save a new pool of Gemini keys."""
        if not keys:
            return 0

        encrypted_blob = GeminiSecurity.encrypt_keys(keys)
        profile = await self.get_or_create_profile(session, user_id)
        profile.gemini_keys_enc = encrypted_blob

        await session.commit()
        await key_rotator.load_keys()
        return len(keys)

    async def discover_models(self, session: AsyncSession, user_id: str) -> List[str]:
        """Fetch available Gemini models and persist to profile."""
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
            profile = await self.get_or_create_profile(session, user_id)
            profile.discovered_models = models
            await session.commit()

        return models

    async def update_model_config(
        self,
        session: AsyncSession,
        user_id: str,
        primary_model: Optional[str],
        waterfall: List[str]
    ) -> None:
        """Update AI model configuration and hot-reload TrinityBridge."""
        profile = await self.get_or_create_profile(session, user_id)
        profile.primary_model = primary_model
        profile.ai_models = waterfall

        await session.commit()

        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
        trinity_bridge.db_primary_model = primary_model
        trinity_bridge.db_waterfall = waterfall
        logger.info(f"[VoiceService] TrinityBridge hot-reloaded for user {user_id}")

    async def update_profile(self, session: AsyncSession, user_id: str, data: Dict[str, object]) -> VoiceProfile:
        """Update or create a voice profile with bulk fields."""
        profile = await self.get_or_create_profile(session, user_id)

        if "wake_words" in data: profile.wake_words = cast(List[str], data["wake_words"])
        if "sleep_words" in data: profile.sleep_words = cast(List[str], data["sleep_words"])
        if "greeting_template" in data: profile.greeting_template = cast(str, data["greeting_template"])
        if "farewell_template" in data: profile.farewell_template = cast(str, data["farewell_template"])
        if "capabilities" in data: profile.capabilities = data["capabilities"]
        if "chat_settings" in data: profile.chat_settings = data["chat_settings"]
        if "primary_model" in data: profile.primary_model = cast(Optional[str], data["primary_model"])
        if "ai_models" in data: profile.ai_models = cast(List[str], data["ai_models"])

        await session.commit()
        return profile

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

# Singleton
voice_service = VoiceService()

# Singleton
voice_service = VoiceService()
