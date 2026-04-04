"""
Client Support Pulse Controller (SSE)
=====================================
Streams AI response events to the specific client session.
Route: GET /api/v1/client/support/pulse/{session_id}

Architecture:
- Real-time event delivery via native SSE.
- Filters events from global EventBus by session_id.
- Zero-Auth (Standardized V2.2 Protocol).
"""
from __future__ import annotations

import json
import asyncio
import logging
from typing import AsyncGenerator

from litestar import Controller, get, Request
from litestar.response import Stream
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

class ClientPulseController(Controller):
    """
    R82.31: Client-side Pulse Delivery via SSE.
    Standardized protocol for 2026 AI Support.
    """
    path = "/api/v1/client/support/pulse"

    @get("/{session_id:str}", guards=[])
    async def stream_pulse(self, request: Request, session_id: str) -> Stream:
        """
        Streams events for a specific support session.
        Uses InternalBus.subscribe_context() for lean, targeted listening.
        """
        
        async def event_generator() -> AsyncGenerator[bytes, None]:
            from backend.services.xohi_memory import xohi_memory
            
            # Initial keep-alive to establish connection
            yield b": link-success\n\n"
            
            if not xohi_memory._use_redis or not xohi_memory.client:
                logger.error("[ClientPulse] Redis is offline. Cannot stream events.")
                return

            pubsub = xohi_memory.client.pubsub()
            channel: str = f"pulse:{session_id}"
            cache_key: str = f"pulse:{session_id}:cache"
            
            # --- PHASE 1: ACTIVE LISTENING (Elite V2.2 Resilience) ---
            # R82.31: We SUBSCRIBE FIRST to ensure we catch the wave while checking the history.
            await pubsub.subscribe(channel)
            logger.info(f"[ClientPulse] Session {session_id} linked to Redis channel {channel} (Pre-emptive).")

            # --- PHASE 2: CATCH-UP (Stateful Pulse) ---
            try:
                cached_data: Union[str, None] = await xohi_memory.client.get(cache_key)
                if cached_data:
                    payload: dict[str, object] = json.loads(cached_data)
                    logger.info(f"[ClientPulse] Cache hit for session {session_id}. Delivering missed event.")
                    
                    # Elite V2.6: Standard Named SSE Format
                    yield b"event: SUPPORT_RESPONSE_READY\n"
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
                    
                    if payload.get("status") == "DONE":
                        logger.info(f"[ClientPulse] Session {session_id} stateful delivery complete. Closing.")
                        return
            except Exception as ce:
                logger.warning(f"[ClientPulse] Cache catch-up failed: {ce}")
            
            # --- PHASE 3: REAL-TIME STREAMING ---
            try:
                while True:
                    try:
                        # R88: Heartbeat/Listen Loop with SSE Protocol logic
                        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                        
                        if message and message['type'] == 'message':
                            payload = json.loads(message['data'])
                            
                            # Elite V2.6: Standard Named SSE Format (Mandatory for Frontend Listeners)
                            yield b"event: SUPPORT_RESPONSE_READY\n"
                            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
                            
                            # Elite V2.2: Dispose Resource immediately on DONE status (RAM 2GB target)
                            if payload.get("status") == "DONE":
                                logger.info(f"[ClientPulse] Session {session_id} real-time response delivered. Closing.")
                                break
                        elif message is None:
                            # Standard Heartbeat
                            yield b": ping\n\n"
                                
                    except asyncio.TimeoutError:
                        yield b": ping\n\n"
                        
            except (asyncio.CancelledError, GeneratorExit):
                logger.debug(f"[ClientPulse] Client disconnected from {channel}.")
            except Exception as e:
                logger.error(f"[ClientPulse] Protocol error: {e}")
            finally:
                await pubsub.unsubscribe(channel)
                logger.info(f"[ClientPulse] Session {session_id} unlinked.")

        # R90: Standardized Headers for Proxy/Cache-Bypass
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
        return Stream(event_generator(), headers=headers)
