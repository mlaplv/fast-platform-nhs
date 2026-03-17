# backend/api/v1/controllers/voice/core.py
import logging
import asyncio
import time
import uuid
import hashlib
from litestar import WebSocket, websocket
from .constants import MIN_AUDIO_BYTES, MAX_AUDIO_BYTES
from .engine import send_partial, transcribe
from .telemetry import background_save_telemetry

logger = logging.getLogger("api-gateway")

@websocket("/ws/stt", guards=[])
async def stt_websocket(socket: WebSocket) -> None:
    """WebSocket endpoint: receive audio chunks, transcribe via Groq Whisper."""
    await socket.accept()

    session_id = socket.query_params.get("session_id", str(uuid.uuid4()))
    logger.info(f"[STT] Client connected (session={session_id[:8]})")

    audio_buffer = bytearray()
    is_active = True
    transcription_lock = asyncio.Lock()
    background_tasks = set()
    last_partial_time = asyncio.get_event_loop().time()
    last_transcribed_size = 0

    try:
        while is_active:
            try:
                msg = await asyncio.wait_for(socket.receive(), timeout=30.0)

                if msg["type"] == "websocket.receive":
                    if "bytes" in msg:
                        data = msg["bytes"]
                        audio_buffer.extend(data)

                        now = asyncio.get_event_loop().time()
                        if now - last_partial_time > 1.0 and len(audio_buffer) > (last_transcribed_size + 2000):
                            last_partial_time = now
                            last_transcribed_size = len(audio_buffer)

                            user_info = getattr(socket.state, "user", None) or socket.scope.get("user")
                            user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None) if user_info else None

                            task = asyncio.create_task(send_partial(socket, bytes(audio_buffer), transcription_lock, user_id))
                            background_tasks.add(task)
                            task.add_done_callback(background_tasks.discard)

                        if len(audio_buffer) % 20000 < len(data):
                            logger.debug(f"[STT] Buffer Memory: {len(audio_buffer)/1024:.1f} KB")
                    elif "text" in msg:
                        data = msg["text"]
                        logger.info(f"[STT] Received command: {data}")
                        if data == "STOP":
                            if len(audio_buffer) > MIN_AUDIO_BYTES:
                                async with transcription_lock:
                                    try:
                                        user_info = getattr(socket.state, "user", None) or socket.scope.get("user")
                                        user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None) if user_info else None

                                        t0 = time.monotonic()
                                        transcript = await transcribe(bytes(audio_buffer), user_id)
                                        duration_ms = int((time.monotonic() - t0) * 1000)

                                        task = asyncio.create_task(background_save_telemetry(
                                            session_id=session_id,
                                            agent_name="Groq-Whisper-STT",
                                            duration_ms=duration_ms,
                                            intent_hash=hashlib.sha256(transcript.encode()).hexdigest()[:16] if transcript else "empty"
                                        ))
                                        background_tasks.add(task)
                                        task.add_done_callback(background_tasks.discard)

                                        await socket.send_json({
                                            "event": "final",
                                            "text": transcript,
                                            "tier": "NEURAL_SYNC"
                                        })
                                    except Exception as e:
                                        logger.error(f"[STT] Transcription path error: {e}")

                            audio_buffer.clear()
                            is_active = False
                            break
                        elif data == "CLOSE":
                            is_active = False
                            break
                elif msg["type"] == "websocket.disconnect":
                    is_active = False
                    break

            except asyncio.TimeoutError:
                await socket.send_json({"event": "timeout", "text": ""})
                break
            except (KeyError, AttributeError) as e:
                logger.debug(f"[STT] Ignored non-data message: {e}")
                continue

            if len(audio_buffer) > MAX_AUDIO_BYTES:
                user_info = getattr(socket.state, "user", None) or socket.scope.get("user")
                user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None) if user_info else None
                transcript = await transcribe(bytes(audio_buffer), user_id)
                await socket.send_json({"event": "final", "text": transcript})
                audio_buffer.clear()
                last_transcribed_size = 0

    except Exception as e:
        if "disconnect" not in str(e).lower():
            logger.error(f"[STT] WebSocket error: {e}")
    finally:
        if len(audio_buffer) > MIN_AUDIO_BYTES:
            try:
                user_info = getattr(socket.state, "user", None) or socket.scope.get("user")
                user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None) if user_info else None
                transcript = await transcribe(bytes(audio_buffer), user_id)
                await socket.send_json({"event": "final", "text": transcript})
            except Exception:
                pass
        logger.info("[STT] Client disconnected")
