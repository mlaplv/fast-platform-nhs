# backend/api/v1/controllers/voice/engine.py
import io
import logging
import asyncio
import unicodedata
from litestar import WebSocket
from backend.services.xohi_memory import xohi_memory
from .constants import (
    WHISPER_MODEL, GROQ_API_KEY, HALLUCINATION_BLACKLIST,
    SENTENCE_SPLIT_RE, DOT_HALLUCINATION_RE
)

logger = logging.getLogger("api-gateway")

async def send_partial(socket: WebSocket, audio_data: bytes, lock: asyncio.Lock, user_id: str = None) -> None:
    """Auxiliary task to send interim transcription results."""
    if lock.locked():
        return

    async with lock:
        try:
            transcript = await transcribe(audio_data, user_id)
            await socket.send_json({"event": "interim", "text": transcript})
        except Exception as e:
            logger.debug(f"[STT] Partial transcription skipped: {e}")

async def transcribe(audio_data: bytes, user_id: str = None) -> str:
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
        system_intents = list(system_mapping.keys())[:10] if system_mapping else []
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
