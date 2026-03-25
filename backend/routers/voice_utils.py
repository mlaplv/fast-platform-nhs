import io
import os
import re
import logging
import asyncio
import httpx
import json
import uuid
import unicodedata
from typing import Dict, Optional, List, cast, Union
from litestar import WebSocket
from backend.services.xohi_memory import xohi_memory
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import AgentTelemetryLogRepository
from backend.database.models import AgentTelemetryLog

logger = logging.getLogger("api-gateway")
async_session_maker = alchemy_config.create_session_maker()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WHISPER_MODEL = "whisper-large-v3-turbo" # Derived from groq/ prefix

# Elite Singleton: Persistent client for zero-latency reconnection
_http_client: Optional[httpx.AsyncClient] = None

def get_stt_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=100))
    return _http_client

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
        audio_file = io.BytesIO(audio_data)

        ext = "webm"
        if audio_data.startswith(b'\x1aE\xdf\xa3'): ext = "webm"
        elif audio_data.startswith(b'OggS'): ext = "ogg"
        elif b'ftyp' in audio_data[:32]: ext = "mp4"

        audio_file.name = f"audio.{ext}"
        response_data: Optional[Dict[str, object]] = None

        stt_anchors = []
        mic_sensitivity = 0.6
        if user_id:
            profile = await xohi_memory.get_voice_profile(user_id)
            if profile:
                stt_anchors = profile.get("stt_anchors", [])
                mic_sensitivity = profile.get("mic_sensitivity", 0.6)

        system_mapping = await xohi_memory.get_system_intent_mapping()
        system_intents = list(cast(Dict[str, object], system_mapping).keys())[:10] if system_mapping else []
        final_anchors = " ".join(stt_anchors + system_intents)
        prompt_text = final_anchors[:500]

        # Direct Groq Whisper API (Elite Direct Integration)
        client = get_stt_client()
        files = {
            "file": (audio_file.name, audio_file, f"audio/{ext}")
        }
        data = {
            "model": WHISPER_MODEL,
            "language": "vi",
            "prompt": prompt_text,
            "temperature": "0.0",
            "response_format": "json"
        }
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        }
        
        api_resp = await client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            files=files,
            data=data,
            headers=headers
        )
        api_resp.raise_for_status()
        response_data = cast(Dict[str, object], api_resp.json())
        
        if not response_data:
            logger.error("[STT] Groq API returned empty payload")
            return ""

        raw_text = response_data.get("text", "")
        if isinstance(raw_text, str):
            transcript = unicodedata.normalize('NFC', raw_text.strip())
        else:
            transcript = ""

        kill_switch_triggered = False
        segments = cast(List[Dict[str, object]], response_data.get("segments", []))

        if segments:
            for seg in segments:
                no_speech = float(cast(Union[float, int, str], seg.get("no_speech_prob") or 0.0))
                comp_ratio = float(cast(Union[float, int, str], seg.get("compression_ratio") or 0.0))
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

    except Exception:
        logger.exception("[STT] Groq transcription failed")
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
