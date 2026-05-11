import asyncio
import logging
import os
import time
from typing import Dict
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.status_codes import HTTP_504_GATEWAY_TIMEOUT
from litestar.enums import MediaType

logger = logging.getLogger("api-gateway.stall-detector")

class StallDetectorMiddleware:
    """
    Elite Stall Detector (V2.2).
    Protects the system from silent hangs (Deadlocks, Infinite Loops).
    If a request takes longer than the threshold, it logs a CRITICAL error 
    and attempts to return a 504 Gateway Timeout.
    """
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        # Default 10 seconds for standard APIs. Can be overridden in .env
        self.timeout = float(os.getenv("REQUEST_STALL_TIMEOUT", "10.0"))
        # Paths to exclude from Stall Detector:
        # - Long-polling / streaming endpoints (unlimited)
        # - AI-heavy synthesis endpoints (have their OWN internal timeouts — do NOT double-kill)
        self.excluded_paths = [
            # Streaming & WebSocket
            "/ws/",
            "/api/v1/stream",
            "/api/v1/intent/stream",
            "/api/v1/client/support/pulse",
            "/api/v1/pulse",
            "/api/v1/tts/stream",
            "/api/v1/client/tts/stream",
            "/api/v1/ads-protection/stream",
            # AI-heavy — self-managed timeouts (R.C.1/R.C.2 in analyst.py)
            "/api/v1/content/scout",
            "/api/v1/content/analyze",
            "/api/v1/content/clean",
            "/api/v1/content/campaigns",   # Campaign-level analyze/* calls
            "/api/v1/client/diagnostics",
            "/api/v1/products/",           # AI Market Sync / SEO Suggest (Slow)
            "/api/v1/admin/ai/models/auto-optimize", # Auto-optimize AI stack (Tests all models)
            # Article AI Generation
            "/api/v1/articles/content-suggest",
            "/api/v1/articles/excerpt-suggest",
            "/api/v1/articles/seo-suggest",
            "/api/v1/articles/faq-suggest",
            # Category AI Generation
            "/api/v1/categories/seo-suggest",
            "/api/v1/categories/faq-suggest",
        ]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        if any(path.startswith(p) for p in self.excluded_paths):
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        
        try:
            # Use asyncio.wait_for to enforce the stall threshold
            await asyncio.wait_for(self.app(scope, receive, send), timeout=self.timeout)
        except asyncio.TimeoutError:
            duration = time.perf_counter() - start_time
            logger.critical(
                f"🚨 [STALL DETECTOR] Request to '{path}' timed out after {duration:.2f}s. "
                "Possible Deadlock or Resource Exhaustion detected!"
            )
            
            # Attempt to send a 504 Response if headers haven't been sent yet
            # In ASGI, we don't know for sure if headers are sent, but we can try.
            # Usually, uvicorn will handle the error if we raise it here.
            await send({
                "type": "http.response.start",
                "status": HTTP_504_GATEWAY_TIMEOUT,
                "headers": [(b"content-type", b"application/json")],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"detail": "Gateway Timeout: Request stalled and was terminated by the Stall Detector.", "trace_id": "STALL-504"}',
                "more_body": False,
            })
        except Exception as e:
            # Re-raise other exceptions to be handled by global_exception_handler
            raise e
