"""WebSocket STT via Groq Whisper — 2026 Voice Pipeline.

Browser sends audio chunks via WebSocket → backend buffers → sends to Groq Whisper → returns transcript.
Replaces Web Speech API (2013) with 95% accuracy Vietnamese STT.

Free tier: 2000 req/day — more than enough for single admin.
"""
import io
import os
import logging
import asyncio
from litestar import WebSocket, websocket

logger = logging.getLogger("api-gateway")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
WHISPER_MODEL = "groq/whisper-large-v3-turbo"
# Minimum audio size to avoid sending silence/noise (bytes)
MIN_AUDIO_BYTES = 5000
# Maximum buffer before force-transcribe (25MB Groq limit)
MAX_AUDIO_BYTES = 20_000_000


@websocket("/ws/stt")
async def stt_websocket(socket: WebSocket) -> None:
    """WebSocket endpoint: receive audio chunks, transcribe via Groq Whisper."""
    await socket.accept()
    logger.info("[STT] Client connected")

    audio_buffer = bytearray()
    is_active = True

    try:
        while is_active:
            try:
                # 2026 Refactor: Use low-level receive() to handle both TEXT (STOP) and BINARY (audio)
                msg = await asyncio.wait_for(socket.receive(), timeout=30.0)
                
                if msg["type"] == "websocket.receive":
                    # For Litestar/Starlette, data is in 'bytes' or 'text'
                    if "bytes" in msg:
                        data = msg["bytes"]
                        # Accumulate audio chunks
                        audio_buffer.extend(data)
                    elif "text" in msg:
                        data = msg["text"]
                        if data == "STOP":
                            # Client signals end of speech — transcribe what we have
                            if len(audio_buffer) > MIN_AUDIO_BYTES:
                                transcript = await _transcribe(bytes(audio_buffer))
                                await socket.send_json({"event": "final", "text": transcript})
                            audio_buffer.clear()
                            continue
                        elif data == "CLOSE":
                            is_active = False
                            break
                elif msg["type"] == "websocket.disconnect":
                    is_active = False
                    break

            except asyncio.TimeoutError:
                # 30s silence → close connection
                await socket.send_json({"event": "timeout", "text": ""})
                break
            except (KeyError, AttributeError) as e:
                logger.debug(f"[STT] Ignored non-data message: {e}")
                continue

            # Safety: force transcribe if buffer too large
            if len(audio_buffer) > MAX_AUDIO_BYTES:
                transcript = await _transcribe(bytes(audio_buffer))
                await socket.send_json({"event": "final", "text": transcript})
                audio_buffer.clear()

    except Exception as e:
        if "disconnect" not in str(e).lower():
            logger.error(f"[STT] WebSocket error: {e}")
    finally:
        # Transcribe remaining audio on disconnect
        if len(audio_buffer) > MIN_AUDIO_BYTES:
            try:
                transcript = await _transcribe(bytes(audio_buffer))
                await socket.send_json({"event": "final", "text": transcript})
            except Exception:
                pass
        logger.info("[STT] Client disconnected")


async def _transcribe(audio_data: bytes) -> str:
    """Send audio to Groq Whisper via litellm and return transcript."""
    try:
        import litellm

        # Create in-memory file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.webm"

        response = await litellm.atranscription(
            model=WHISPER_MODEL,
            file=audio_file,
            language="vi",
            api_key=GROQ_API_KEY,
        )

        transcript = response.text.strip() if hasattr(response, "text") else ""
        logger.info(f"[STT] Groq Whisper: '{transcript}' ({len(audio_data)} bytes)")
        return transcript

    except Exception as e:
        logger.error(f"[STT] Groq transcription failed: {e}")
        return ""
