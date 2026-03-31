import json
import asyncio
import logging
from typing import AsyncGenerator
from uuid import UUID
from litestar import Controller, get, Request
from litestar.response import Stream
from backend.services.event_bus import event_bus

from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

logger = logging.getLogger("api-gateway")

class ContentStreamController(Controller):
    path = "/api/v1/content/stream"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    @get("/{campaign_id:uuid}")
    async def stream_campaign(self, campaign_id: UUID) -> Stream:
        """Stream campaign events (Standardized V2.2)."""
        cid_str = str(campaign_id)
        
        async def event_generator() -> AsyncGenerator[bytes, None]:
            # R76: Queue safety (Limit to 100 events)
            queue = asyncio.Queue(maxsize=100)
            
            async def filter_callback(payload: dict):
                if payload.get("campaign_id") == cid_str:
                    try:
                        queue.put_nowait(payload)
                    except asyncio.QueueFull:
                        pass

            # R82.1: Lifecycle Management
            start_time = asyncio.get_event_loop().time()
            max_age = 1800  # 30-minute hard cut-off for content streams (Ultra Lean)

            event_bus.subscribe("CONTENT_PROGRESS", filter_callback)
            event_bus.subscribe("CONTENT_CHUNK", filter_callback)
            event_bus.subscribe("CONTENT_STEP_COMPLETED", filter_callback)
            event_bus.subscribe("CAMPAIGN_PURGED", filter_callback)
            event_bus.subscribe("MEDIA_ANALYZED", filter_callback)
            
            logger.info(f"[ContentStream] Linked to campaign {cid_str}")

            try:
                yield b": initial-sync\n\n"
                
                while True:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > max_age:
                        logger.info(f"[ContentStream] Cut-off for {cid_str} (30m).")
                        yield b"event: terminate\ndata: {\"message\": \"Stream duration limit reached.\"}\n\n"
                        break

                    try:
                        # R82: Standardized 15s Heartbeat
                        payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                        
                        if payload.get("type") == "TERMINATE" or payload.get("action") == "PURGE":
                            yield b"event: terminate\ndata: {\"message\": \"Stream closed by orchestrator.\"}\n\n"
                            break

                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
                        
                    except asyncio.TimeoutError:
                        yield b": ping\n\n"
            except (asyncio.CancelledError, GeneratorExit):
                pass
            except Exception as e:
                logger.error(f"[ContentStream] Error {cid_str}: {e}")
            finally:
                event_bus.unsubscribe("CONTENT_PROGRESS", filter_callback)
                event_bus.unsubscribe("CONTENT_CHUNK", filter_callback)
                event_bus.unsubscribe("CONTENT_STEP_COMPLETED", filter_callback)
                event_bus.unsubscribe("CAMPAIGN_PURGED", filter_callback)
                event_bus.unsubscribe("MEDIA_ANALYZED", filter_callback)
                logger.info(f"[ContentStream] Unlinked from campaign {cid_str}")

        # R90: Standardized Proxy Headers
        headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        }
        return Stream(event_generator(), headers=headers)
