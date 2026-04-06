# backend/routers/voice_core.py
import logging
import asyncio
import time
import uuid
import hashlib
from typing import Optional, Dict, Any, Union
from litestar import WebSocket, websocket
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from .voice_utils import (
    MIN_AUDIO_BYTES, MAX_AUDIO_BYTES,
    send_partial, transcribe, background_save_telemetry
)
from backend.constants.permissions import PermissionEnum
from backend.guards import PermissionGuard
from backend.middleware import UserPayload

logger = logging.getLogger("api-gateway")

def get_user_info(socket: WebSocket) -> Optional[Dict[str, Any]]:
    """Helper to safely extract user from socket scope with V2.2 hierarchy."""
    return socket.scope.get("state", {}).get("user") or getattr(socket.state, "user", None)

def get_user_id(socket: WebSocket) -> Optional[str]:
    """Helper to safely extract user_id for telemetry."""
    user = get_user_info(socket)
    if isinstance(user, dict):
        return user.get("id")
    return getattr(user, "id", None) if user else None

@websocket("/ws/stt")
async def stt_websocket(socket: WebSocket) -> None:
    """WebSocket endpoint: receive audio chunks, transcribe via Groq Whisper."""
    # 🛡️ [STT-Elite] Phase 3: Immediate Handshake Acceptance (CTO Protocol)
    await socket.accept()
    logger.info("🛡️ [STT-TRACE] Connection Accepted. Entering identity verification...")

    user: Optional[UserPayload] = get_user_info(socket) # type: ignore
    
    if not user:
        logger.warning(f"🚨 [STT] Handshake REJECTED after accept: No user state in scope.")
        await socket.send_json({"event": "error", "message": "Vui lòng đăng nhập lại (VUI-Missing-Identity)"})
        await socket.close()
        return

    # PBAC Check (Elite Rule R00)
    is_super: bool = "SUPER_ADMIN" in user.get("roles", [])
    has_voice: bool = "ai:config" in user.get("perms", []) or "system:all" in user.get("perms", [])
    
    if not (is_super or has_voice):
        logger.warning(f"⛔ [STT] Handshake REJECTED: Insufficient permissions for {user.get('email')}")
        await socket.send_json({"event": "error", "message": "Security Clearance Level Insufficient"})
        await socket.close()
        return

    session_id: str = socket.query_params.get("session_id") or str(uuid.uuid4())
    logger.info(f"✅ [STT-Elite] Handshake Finalized: session={session_id[:8]} user={user.get('email')}")

    audio_buffer: bytearray = bytearray()
    is_active: bool = True
    transcription_lock: asyncio.Lock = asyncio.Lock()
    background_tasks: set = set()
    last_partial_time: float = float(asyncio.get_running_loop().time())
    last_transcribed_size: int = 0

    start_time_mono = time.monotonic()
    max_age = 600  # 10-minute hard limit for STT sessions (Elite Rule)

    try:
        while is_active:
            # R82.1: Lifecycle check
            if (time.monotonic() - start_time_mono) > max_age:
                logger.warning(f"[STT] Max age reached ({max_age}s). Closing.")
                await socket.send_json({"event": "error", "message": "Phiên làm việc quá dài, Sếp vui lòng bật lại nhé."})
                break

            try:
                # R82: Standardized 15s timeout for heartbeat logic
                msg = await asyncio.wait_for(socket.receive(), timeout=15.0)

                if msg["type"] == "websocket.receive":
                    if "bytes" in msg:
                        data = msg["bytes"]
                        audio_buffer.extend(data)

                        now = float(asyncio.get_running_loop().time())
                        if now - last_partial_time > 1.0 and len(audio_buffer) > (last_transcribed_size + 2000):
                            last_partial_time = now
                            last_transcribed_size = len(audio_buffer)

                            user_id = get_user_id(socket)

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
                                        user_id = get_user_id(socket)

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
                # Standardized WebSocket Ping/Pong handled by Litestar, but we can send a custom ping if needed
                # However, 15s no-data results in a soft timeout to keep things lean
                await socket.send_json({"event": "ping", "timestamp": time.time()})
                continue
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
            except Exception as final_error:
                logger.error(f"[STT] Final transcription cleanup failed: {final_error}")
        logger.info("[STT] Client disconnected")
