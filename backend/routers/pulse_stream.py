import json
import asyncio
import logging
from typing import AsyncGenerator
from litestar import Controller, get
from litestar.response import Stream
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

class PulseStreamController(Controller):
    """
    R82.32: Agent Pulse SSE Endpoint.
    Streams system-wide events (Progress, Completion, Alerts) to the UI in real-time.
    Replaces Pusher with a native, zero-dependency streaming architecture.
    """
    path = "/api/v1/pulse"

    @get("/stream")
    async def stream_pulse(self) -> Stream:
        """Stream system events via Native SSE (Standardized V2.2)."""
        
        async def event_generator() -> AsyncGenerator[bytes, None]:
            # R76: Queue safety (Limit to 100 events to prevent memory bloat)
            queue = asyncio.Queue(maxsize=100)
            event_bus.subscribe_broadcast(queue)
            logger.info("[PulseStream] Client linked to Agent Pulse.")
            
            start_time = asyncio.get_event_loop().time()
            max_age = 4 * 3600  # 4-hour hard cut-off to prevent "infinite" zombie leaks (User Rule)
            
            try:
                # Immediate keep-alive + protocol headers handled by return Stream()
                yield b": initial-sync\n\n"
                
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > max_age:
                        logger.info("[PulseStream] Reaching max age (4h). Closing for recycling.")
                        yield b"event: recycle\ndata: {\"message\": \"Connection age limit reached. Please reconnect.\"}\n\n"
                        break

                    try:
                        # R82: Standardized 15s Heartbeat (Proxy Friendly)
                        event = await asyncio.wait_for(queue.get(), timeout=15.0)
                        
                        data = {
                            "event": event.name,
                            "payload": event.payload,
                            "timestamp": event.timestamp
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")
                        
                    except asyncio.TimeoutError:
                        # Keep-alive ping (Standardized)
                        yield b": ping\n\n"
            except (asyncio.CancelledError, GeneratorExit):
                logger.info("[PulseStream] Client disconnected (Normal).")
            except Exception as e:
                logger.error(f"[PulseStream] Connection error: {e}")
            finally:
                event_bus.unsubscribe_broadcast(queue)
                logger.info("[PulseStream] Client unlinked.")

        # R90: Explicit SSE Headers to bypass proxy buffering and protocol conflicts
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Critical for Nginx/Caddy
            "X-Content-Type-Options": "nosniff", # Prevent MIME sniffing
        }
        return Stream(event_generator(), headers=headers)
