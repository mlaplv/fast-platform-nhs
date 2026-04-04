import json
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any
from litestar import Controller, get, Request
from litestar.response import Stream
from backend.services.event_bus import event_bus

from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

def mask_pii(event_name: str, payload: dict) -> dict:
    """R82.33: Security Shield — Mask PII in broadcast events."""
    if event_name == "ORDER_CREATED":
        p = dict(payload)
        # Mask phone: 094***1122
        phone = p.get("phone", "")
        if len(phone) > 6:
            p["phone"] = f"{phone[:3]}***{phone[-4:]}"
        
        # Mask customer name: N*** A** Tuan
        name = p.get("customer", "")
        if name:
            parts = name.split()
            if len(parts) > 1:
                p["customer"] = f"{parts[0][0]}*** {parts[-1]}"
            else:
                p["customer"] = f"{name[0]}***"
        
        # Mask address: 123 Street... -> 123...
        addr = p.get("address", "")
        if addr:
            p["address"] = f"{addr[:6]}..."
            
        # Remove IP and User Agent from broadcast
        p.pop("ip", None)
        p.pop("user_agent", None)
        return p
    return payload

class PulseStreamController(Controller):
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]
    """
    R82.32: Agent Pulse SSE Endpoint.
    Streams system-wide events (Progress, Completion, Alerts) to the UI in real-time.
    Replaces Pusher with a native, zero-dependency streaming architecture.
    """
    path = "/api/v1/pulse"

    @get("/stream")
    async def stream_pulse(self, request: Request) -> Stream:
        """Stream system events via Native SSE (Standardized V2.2)."""
        
        async def event_generator(scope: dict) -> AsyncGenerator[bytes, None]:
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
                        
                        # R82.33: Security — Mask PII unless SUPER_ADMIN
                        user = scope.get("state", {}).get("user", {})
                        is_super = "SUPER_ADMIN" in user.get("roles", [])
                        
                        payload = event.payload
                        if not is_super:
                            payload = mask_pii(event.name, payload)

                        data = {
                            "event": event.name,
                            "payload": payload,
                            "timestamp": event.timestamp
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")
                        
                    except asyncio.TimeoutError:
                        # R82: Standardized Heartbeat Event (Frontend Observable)
                        yield b"event: HEARTBEAT\ndata: {}\n\n"
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
            "X-Accel-Buffering": "no",  # Critical for Nginx/Caddy
            "X-Content-Type-Options": "nosniff", # Prevent MIME sniffing
        }
        return Stream(event_generator(request.scope), headers=headers)
