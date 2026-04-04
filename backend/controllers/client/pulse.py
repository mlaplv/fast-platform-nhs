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
            # Subscribe to the event bus with a context-managed queue
            async with event_bus.subscribe_context("SUPPORT_RESPONSE_READY") as queue:
                logger.info("[ClientPulse] Session %s linked to Pulse.", session_id)
                
                # Initial keep-alive to establish connection
                yield f": link-success for session {session_id}\n\n".encode("utf-8")
                
                try:
                    while True:
                        try:
                            # Wait for event with a heartbeat timeout
                            payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                            
                            # R82.31: Filter by session_id to ensure privacy
                            if payload.get("session_id") == session_id:
                                data = {
                                    "event": "SUPPORT_RESPONSE_READY",
                                    "payload": payload,
                                }
                                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")
                                
                                # Once DONE event is sent, we can technically close,
                                # but usually we keep it open for follow-ups or multiple chunks.
                                # For Elite V2.2, we close after completion to save RAM (2GB limit).
                                if payload.get("status") == "DONE":
                                    logger.info("[ClientPulse] Session %s response delivered. Closing.", session_id)
                                    break
                                    
                        except asyncio.TimeoutError:
                            # Standard Heartbeat
                            yield b": ping\n\n"
                            
                except (asyncio.CancelledError, GeneratorExit):
                    logger.debug("[ClientPulse] Client disconnected.")
                except Exception as e:
                    logger.error("[ClientPulse] Protocol error: %s", e)
                finally:
                    logger.info("[ClientPulse] Session %s unlinked.", session_id)

        # R90: Standardized Headers for Proxy/Cache-Bypass
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
        return Stream(event_generator(), headers=headers)
