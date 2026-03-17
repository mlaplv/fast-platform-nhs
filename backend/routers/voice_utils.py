# backend/routers/voice_utils.py
import io
import os
import re
import logging
import asyncio
import uuid
import unicodedata
from typing import Dict, Optional, List, cast
from litestar import WebSocket
from backend.services.xohi_memory import xohi_memory
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import AgentTelemetryLogRepository
from backend.database.models import AgentTelemetryLog

logger = logging.getLogger("api-gateway")
async_session_maker = alchemy_config.create_session_maker()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WHISPER_MODEL = "groq/whisper-large-v3-turbo"

# Minimum audio size to avoid sending silence/noise (bytes)
MIN_AUDIO_BYTES = 1500
# Maximum buffer before force-transcribe (25MB Groq limit)
MAX_AUDIO_BYTES = 20_000_000

# Zero-Hallucination 2026: Blacklist for common Whisper phantoms in silence/noise
HALLUCINATION_BLACKLIST = [
    "cám ơn các bạn", "subscribe", "đăng ký kênh", "ghiền mì gõ",
    "chào các bạn", "phimmoichill", "website chính thức",
    "liên hệ với chúng tôi", "video", "youtube", "mọi người",
    "ủng hộ", "bình luận", "zalo", "facebook", "website", "chào mừng",
    "tập trung vào ngữ cảnh"
]

SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')
DOT_HALLUCINATION_RE = re.compile(r'^\.+$')

async def send_partial(socket: WebSocket, audio_data: bytes, lock: asyncio.Lock, user_id: Optional[str] = None) -> None:
    """Auxiliary task to send interim transcription results."""
    if lock.locked():
        return

    async with lock:
        try:
            transcript = await transcribe(audio_data, user_id)
            await socket.send_json({"event": "interim", "text": transcript})
        except Exception as e:
            logger.debug(f"[STT] Partial transcription skipped: {e}")

async def transcribe(audio_data: bytes, user_id: Optional[str] = None) -> str:
    """Send audio to Groq Whisper via litellm and return transcript."""
    try:
        import litellm
        audio_file = io.BytesIO(audio_data)

        ext = "webm"
        if audio_data.startswith(b'\x1aE\xdf\xa3'): ext = "webm"
        elif audio_data.startswith(b'OggS'): ext = "ogg"
        elif b'ftyp' in audio_data[:32]: ext = "mp4"

        audio_file.name = f"audio.{ext}"

        stt_anchors = []
        mic_sensitivity = 0.6
        if user_id:
            profile = await xohi_memory.get_voice_profile(user_id)
            if profile:
                stt_anchors = profile.get("stt_anchors", [])
                mic_sensitivity = profile.get("mic_sensitivity", 0.6)

        system_mapping = await xohi_memory.get_system_intent_mapping()
        system_intents = list(cast(Dict, system_mapping).keys())[:10] if system_mapping else []
        final_anchors = " ".join(stt_anchors + system_intents)
        prompt_text = final_anchors[:500]

        response = await litellm.atranscription(
            model=WHISPER_MODEL,
            file=audio_file,
            language="vi",
            api_key=GROQ_API_KEY,
            prompt=prompt_text,
            temperature=0.0,
            response_format="verbose_json"
        )

        raw_text = getattr(response, "text", "")
        if isinstance(raw_text, str):
            transcript = unicodedata.normalize('NFC', raw_text.strip())
        else:
            transcript = ""

        kill_switch_triggered = False
        segments = getattr(response, "segments", []) or (response.get("segments", []) if isinstance(response, dict) else [])
        for seg in segments:
            no_speech = seg.get("no_speech_prob", 0.0)
            comp_ratio = seg.get("compression_ratio", 0.0)
            if no_speech > mic_sensitivity or comp_ratio > 2.4:
                logger.warning(f"[STT] Kill-Switch triggered! no_speech={no_speech:.2f}, comp_ratio={comp_ratio:.2f}. Suppressing block.")
                kill_switch_triggered = True
                break

        if kill_switch_triggered:
            return ""

        if transcript:
            parts = [p.strip() for p in SENTENCE_SPLIT_RE.split(transcript) if p.strip()]
            unique_parts = []
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
                    logger.warning(f"[STT] Hallucination stripped: '{p}'")

            if not clean_parts:
                return ""

            transcript = " ".join(clean_parts)

        if transcript:
            logger.info(f"[STT] Groq Whisper: '{transcript}' ({len(audio_data)} bytes)")

        return transcript

    except Exception as e:
        logger.error(f"[STT] Groq transcription failed: {e}")
        return ""

async def background_save_telemetry(
    session_id: str,
    agent_name: str,
    duration_ms: int,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_token: float = 0.0,
    intent_hash: str = "stt_op"
) -> None:
    """Save performance metrics to database in background."""
    try:
        async with async_session_maker() as session:
            repo = AgentTelemetryLogRepository(session=session)
            await repo.add(AgentTelemetryLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                agent_name=agent_name,
                intent_hash=intent_hash,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_token=cost_token,
                duration_ms=duration_ms
            ))
            await session.commit()
    except Exception as e:
        logger.error(f"[STT Telemetry Error] {e}")
