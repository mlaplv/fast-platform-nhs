import json
import asyncio
import logging
from typing import AsyncGenerator
from uuid import UUID
from litestar import Controller, get
from litestar.response import Stream
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

class ContentStreamController(Controller):
    """
    V76.5: Neural Streaming Waterfall for Content Campaigns.
    Provides sub-second real-time updates for a specific campaign.
    """
    path = "/api/v1/content/stream"

    @get("/{campaign_id:uuid}")
    async def stream_campaign(self, campaign_id: UUID) -> Stream:
        """Stream campaign events (Progress, Chunks, Completion) via Native SSE."""
        cid_str = str(campaign_id)

        async def event_generator() -> AsyncGenerator[bytes, None]:
            # Use specific event types but we'll filter them by campaign_id
            # Listening to multiple event types via event_bus subscription
            queue = asyncio.Queue(maxsize=100)

            async def filter_callback(payload: dict):
                if payload.get("campaign_id") == cid_str:
                    try:
                        queue.put_nowait(payload)
                    except asyncio.QueueFull:
                        pass

            # Subscribe to relevant events
            event_bus.subscribe("CONTENT_PROGRESS", filter_callback)
            event_bus.subscribe("CONTENT_CHUNK", filter_callback)
            event_bus.subscribe("CONTENT_STEP_COMPLETED", filter_callback)

            logger.info(f"[ContentStream] Client connected to stream for campaign {cid_str}")

            try:
                # Keep-alive ping
                yield b": ping\n\n"

                while True:
                    try:
                        # Wait for an event
                        payload = await asyncio.wait_for(queue.get(), timeout=45.0)

                        # We don't have the event name in the payload directly in a way that SSE likes,
                        # but we can infer or include it.
                        # For simplicity, we just send the payload as data.
                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")

                    except asyncio.TimeoutError:
                        yield b": ping\n\n"
            except Exception as e:
                logger.error(f"[ContentStream] Connection error for {cid_str}: {e}")
            finally:
                event_bus.unsubscribe("CONTENT_PROGRESS", filter_callback)
                event_bus.unsubscribe("CONTENT_CHUNK", filter_callback)
                event_bus.unsubscribe("CONTENT_STEP_COMPLETED", filter_callback)
                logger.info(f"[ContentStream] Client disconnected from campaign {cid_str}")

        return Stream(event_generator(), media_type="text/event-stream")
