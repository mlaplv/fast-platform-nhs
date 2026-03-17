"""WebSocket STT via Groq Whisper — 2026 Voice Pipeline.

Browser sends audio chunks via WebSocket → backend buffers → sends to Groq Whisper → returns transcript.
Replaces Web Speech API (2013) with 95% accuracy Vietnamese STT.

Free tier: 2000 req/day — more than enough for single admin.
"""
import logging
import asyncio
from litestar import WebSocket, websocket
from backend.services.voice_service import voice_service

logger = logging.getLogger("api-gateway")

# Maximum buffer before force-transcribe (25MB Groq limit)
MAX_AUDIO_BYTES = 20_000_000

@websocket("/ws/stt", guards=[])
async def stt_websocket(socket: WebSocket) -> None:
    """WebSocket endpoint: receive audio chunks, transcribe via VoiceService."""
    await socket.accept()
    logger.info("[STT] Client connected")

    audio_buffer = bytearray()
    is_active = True
    transcription_lock = asyncio.Lock() # Serializer to prevent jitter/out-of-order partials
    background_tasks = set() # Track tasks to avoid memory leaks (V76)
    last_partial_time = asyncio.get_event_loop().time()
    last_transcribed_size = 0

    try:
        while is_active:
            try:
                # 2026 Refactor: Use low-level receive() to handle both TEXT (STOP) and BINARY (audio)
                msg = await asyncio.wait_for(socket.receive(), timeout=30.0)

                if msg["type"] == "websocket.receive":
                    if "bytes" in msg:
                        data = msg["bytes"]
                        audio_buffer.extend(data)

                        # ZERO-DELAY LOGIC: Partial transcription every ~1.0s (Hybrid Optimization)
                        now = asyncio.get_event_loop().time()
                        if now - last_partial_time > 1.0 and len(audio_buffer) > (last_transcribed_size + 2000):
                            last_partial_time = now
                            last_transcribed_size = len(audio_buffer)

                            # Extract user info
                            user_info = getattr(socket.state, "user", None) or socket.scope.get("user")
                            user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None) if user_info else None

                            task = asyncio.create_task(_send_partial(socket, bytes(audio_buffer), transcription_lock, user_id))
                            background_tasks.add(task)
                            task.add_done_callback(background_tasks.discard)

                        if len(audio_buffer) % 20000 < len(data):
                            logger.debug(f"[STT] Buffer Memory: {len(audio_buffer)/1024:.1f} KB")
                    elif "text" in msg:
                        data = msg["text"]
                        logger.info(f"[STT] Received command: {data}")
                        if data == "STOP":
                            logger.info(f"[STT] Finalizing transcription (buffer={len(audio_buffer)} bytes)")
                            if audio_buffer:
                                async with transcription_lock:
                                    try:
                                        user_info = getattr(socket.state, "user", None) or socket.scope.get("user")
                                        user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None) if user_info else None

                                        transcript, corrections = await voice_service.transcribe_and_correct(
                                            bytes(audio_buffer),
                                            user_id=user_id,
                                            is_partial=False
                                        )

                                        logger.info(f"[STT] Final transcript received: '{transcript}'")
                                        await socket.send_json({
                                            "event": "final",
                                            "text": transcript,
                                            "corrections": corrections,
                                            "tier": "NEURAL_SYNC"
                                        })
                                    except Exception as e:
                                        logger.error(f"[STT] Finalization error: {e}")

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
                await socket.send_json({"event": "timeout", "text": ""})
                break
            except (KeyError, AttributeError) as e:
                logger.debug(f"[STT] Ignored non-data message: {e}")
                continue

            # Safety: force transcribe if buffer too large
            if len(audio_buffer) > MAX_AUDIO_BYTES:
                user_info = getattr(socket.state, "user", None) or socket.scope.get("user")
                user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None) if user_info else None
                transcript, _ = await voice_service.transcribe_and_correct(bytes(audio_buffer), user_id=user_id)
                await socket.send_json({"event": "final", "text": transcript})
                audio_buffer.clear()
                last_transcribed_size = 0

    except Exception as e:
        if "disconnect" not in str(e).lower():
            logger.error(f"[STT] WebSocket error: {e}")
    finally:
        if audio_buffer:
            try:
                user_info = getattr(socket.state, "user", None) or socket.scope.get("user")
                user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None) if user_info else None
                transcript, _ = await voice_service.transcribe_and_correct(bytes(audio_buffer), user_id=user_id)
                await socket.send_json({"event": "final", "text": transcript})
            except Exception:
                pass
        logger.info("[STT] Client disconnected")

async def _send_partial(socket: WebSocket, audio_data: bytes, lock: asyncio.Lock, user_id: str = None) -> None:
    """Auxiliary task to send interim transcription results."""
    if lock.locked():
        return

    async with lock:
        try:
            transcript, _ = await voice_service.transcribe_and_correct(
                audio_data,
                user_id=user_id,
                is_partial=True
            )
            await socket.send_json({"event": "interim", "text": transcript})
        except Exception as e:
            logger.debug(f"[STT] Partial transcription skipped: {e}")

