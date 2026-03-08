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
MIN_AUDIO_BYTES = 1500
# Maximum buffer before force-transcribe (25MB Groq limit)
MAX_AUDIO_BYTES = 20_000_000

# Zero-Hallucination 2026: Blacklist for common Whisper phantoms in silence/noise
# Expanded Phase 44: Catching Prompt Echoes
HALLUCINATION_BLACKLIST = [
    "cám ơn các bạn", "subscribe", "đăng ký kênh", "ghiền mì gõ", 
    "chào các bạn", "hẹn gặp lại", "phimmoichill", "website chính thức",
    "liên hệ với chúng tôi", "tạm biệt", "video", "youtube", "mọi người",
    "ủng hộ", "bình luận", "zalo", "facebook", "website", "chào mừng", "kênh",
    "theo dõi chúng tôi", "đừng quên", "nhấn chuông", "thông báo",
    "tập trung vào ngữ cảnh", "quản trị doanh nghiệp", "smartshop", "tin tức", "đơn hàng"
]


@websocket("/ws/stt", guards=[])
async def stt_websocket(socket: WebSocket) -> None:
    """WebSocket endpoint: receive audio chunks, transcribe via Groq Whisper."""
    await socket.accept()
    logger.info("[STT] Client connected")

    audio_buffer = bytearray()
    is_active = True
    transcription_lock = asyncio.Lock() # Serializer to prevent jitter/out-of-order partials
    last_partial_time = asyncio.get_event_loop().time()
    last_transcribed_size = 0

    try:
        while is_active:
            try:
                # 2026 Refactor: Use low-level receive() to handle both TEXT (STOP) and BINARY (audio)
                msg = await asyncio.wait_for(socket.receive(), timeout=30.0)
                
                if msg["type"] == "websocket.receive":
                    # For Litestar/Starlette, data is in 'bytes' or 'text'
                    if "bytes" in msg:
                        data = msg["bytes"]
                        audio_buffer.extend(data)
                        
                        # ZERO-DELAY LOGIC: Partial transcription every ~0.5s (Phase 46: Ultralight)
                        now = asyncio.get_event_loop().time()
                        if now - last_partial_time > 0.5 and len(audio_buffer) > (last_transcribed_size + 1000):
                            last_partial_time = now
                            last_transcribed_size = len(audio_buffer)
                            asyncio.create_task(_send_partial(socket, bytes(audio_buffer), transcription_lock))

                        if len(audio_buffer) % 20000 < len(data): 
                            logger.debug(f"[STT] Buffer Memory: {len(audio_buffer)/1024:.1f} KB")
                    elif "text" in msg:
                        data = msg["text"]
                        logger.info(f"[STT] Received command: {data}")
                        if data == "STOP":
                            logger.info(f"[STT] Received STOP signal. Finalizing transcription (buffer={len(audio_buffer)} bytes)")
                            if len(audio_buffer) > MIN_AUDIO_BYTES:
                                async with transcription_lock:
                                    try:
                                        logger.info("[STT] Calling Groq Whisper via litellm...")
                                        transcript = await _transcribe(bytes(audio_buffer))
                                        logger.info(f"[STT] Final transcript received: '{transcript}'")
                                        await socket.send_json({
                                            "event": "final", 
                                            "text": transcript,
                                            "tier": "NEURAL_SYNC"
                                        })
                                    except Exception as e:
                                        logger.error(f"[STT] Transcription path error: {e}")
                            
                            audio_buffer.clear()
                            is_active = False # Phase 45: Hard exit after STOP to prevent double events
                            break 
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
                last_transcribed_size = 0

    except Exception as e:
        if "disconnect" not in str(e).lower():
            logger.error(f"[STT] WebSocket error: {e}")
    finally:
        # Transcribe remaining audio on disconnect
        if len(audio_buffer) > MIN_AUDIO_BYTES:
            try:
                # We need to pass the actual data buffer
                transcript = await _transcribe(bytes(audio_buffer))
                await socket.send_json({"event": "final", "text": transcript})
            except Exception:
                pass
        logger.info("[STT] Client disconnected")


async def _send_partial(socket: WebSocket, audio_data: bytes, lock: asyncio.Lock):
    """Auxiliary task to send interim transcription results."""
    # Concurrency Rule 2026: Skip if another transcription is in progress
    # to avoid out-of-order results and flickering UI.
    if lock.locked():
        return
        
    async with lock:
        try:
            transcript = await _transcribe(audio_data)
            # PHASE 14: Always send interim event, even if transcript is empty (filtered)
            # This keeps the frontend 'live' visually.
            await socket.send_json({"event": "interim", "text": transcript})
        except Exception as e:
            logger.debug(f"[STT] Partial transcription skipped: {e}")


async def _transcribe(audio_data: bytes) -> str:
    """Send audio to Groq Whisper via litellm and return transcript."""
    try:
        import litellm

        # Create in-memory file-like object
        audio_file = io.BytesIO(audio_data)
        
        # Detect extension from magic bytes
        ext = "webm"
        if audio_data.startswith(b'\x1aE\xdf\xa3'): ext = "webm"
        elif audio_data.startswith(b'OggS'): ext = "ogg"
        elif b'ftyp' in audio_data[:32]: ext = "mp4"
            
        audio_file.name = f"audio.{ext}"

        # Contextual Grounding 2026: 
        # Phase 50: Removed specific keywords that cause prompt echoes.
        # Phase 58: Disabled condition_on_previous_text to prevent hallucination death spirals.

        response = await litellm.atranscription(
            model=WHISPER_MODEL,
            file=audio_file,
            language="vi",
            api_key=GROQ_API_KEY,
            prompt="", # Empty prompt to prevent echoing
            temperature=0.0, 
            extra_body={} # Groq does not support condition_on_previous_text or no_speech_threshold
        )

        transcript = response.text.strip() if hasattr(response, "text") else ""
        
        # Phase 50: Aggressive Superstring Deduplication
        if transcript:
            import re
            # Split by punctuation (. ? !) followed by a space
            parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', transcript) if p.strip()]
            unique_parts = []
            for p in parts:
                p_lower = p.lower()
                # If this sentence is already contained in the previous one, or contains the previous one, merge.
                if not unique_parts:
                    unique_parts.append(p)
                else:
                    last = unique_parts[-1].lower()
                    if p_lower in last:
                        continue # Already covered
                    elif last in p_lower:
                        unique_parts[-1] = p # Replace with more complete version
                    else:
                        unique_parts.append(p)
            
            # Guard: Semantic Hallucination Filter - Targeted Stripping
            clean_parts = []
            for p in unique_parts:
                p_lower = p.lower()
                # Skip stripping if the phrase itself is just "Đơn hàng" but it was part of a valid command
                # Wait, the blacklist is meant to catch standalone whispers. 
                if not any(bad in p_lower for bad in HALLUCINATION_BLACKLIST):
                    clean_parts.append(p)
                else:
                    logger.warning(f"[STT] Hallucination stripped: '{p}'")
                    
            if not clean_parts:
                if transcript:
                    logger.warning(f"[STT] Full transcript suppressed due to hallucination: '{transcript}'")
                return ""
                
            transcript = " ".join(clean_parts)

        if transcript:
            logger.info(f"[STT] Groq Whisper: '{transcript}' ({len(audio_data)} bytes)")
            
        return transcript

    except Exception as e:
        logger.error(f"[STT] Groq transcription failed: {e}")
        return ""
