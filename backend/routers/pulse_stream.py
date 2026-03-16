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
        """Stream system events via Native SSE."""
        
        async def event_generator() -> AsyncGenerator[bytes, None]:
            queue = asyncio.Queue()
            event_bus.subscribe_broadcast(queue)
            logger.info("[PulseStream] New client connected to Agent Pulse.")
            
            try:
                # Keep-alive ping to prevent connection timeout
                yield b": ping\n\n"
                
                while True:
                    try:
                        # Wait for an event with a timeout for heartbeat
                        event = await asyncio.wait_for(queue.get(), timeout=30.0)
                        
                        # Format as SSE
                        data = {
                            "event": event.name,
                            "payload": event.payload,
                            "timestamp": event.timestamp
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")
                        
                    except asyncio.TimeoutError:
                        # Send keep-alive
                        yield b": ping\n\n"
            except asyncio.CancelledError:
                # Handle client disconnection gracefully without logging as an error
                logger.info("[PulseStream] Client connection cancelled (normal disconnection).")
            except Exception as e:
                logger.error(f"[PulseStream] Connection error: {e}")
            finally:
                event_bus.unsubscribe_broadcast(queue)
                logger.info("[PulseStream] Client disconnected from Agent Pulse.")

        # Disable default read timeout to allow infinite SSE stream (relying on heartbeat pings)
        return Stream(event_generator(), media_type="text/event-stream")
