import os
import time
from typing import Optional, Final, Dict
from litestar import Controller, get, post, Request
from litestar.response import Stream
from litestar.exceptions import PermissionDeniedException, TooManyRequestsException
from pydantic import BaseModel, Field, ConfigDict
from backend.services.client_tts import stream_tts_public

# R5.0: IP Rate Limiting State (In-Memory for 4GB limit)
# CNS V5.0: Using a simple dict for rate tracking.
RATE_LIMIT_STORE: Dict[str, list[float]] = {}
LIMIT_WINDOW: Final[int] = 60  # 1 minute
LIMIT_MAX_REQUESTS: Final[int] = 5  # Max 5 calls per minute

class TTSRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str = Field(..., min_length=1, max_length=3000)


class PublicTTSController(Controller):
    path: Final[str] = "/api/v1/client/tts"

    @get("/stream", sync_to_thread=False)
    async def get_public_tts_stream_get(self, request: Request, text: Optional[str] = None) -> Stream:
        """Public TTS endpoint via GET."""
        self._validate_request(request)
        input_text: str = text if text else ""
        return self._create_tts_stream(input_text)

    @post("/stream", sync_to_thread=False)
    async def get_public_tts_stream_post(self, request: Request, data: TTSRequest) -> Stream:
        """Public TTS endpoint via POST."""
        self._validate_request(request)
        return self._create_tts_stream(data.text)

    def _validate_request(self, request: Request) -> None:
        """
        Lockdown Defense V5.1: micsmo.com EXCLUSIVITY.
        Only authorized domains can access the Voice Engine.
        """
        # 1. Domain Exclusivity Check (Anti-Stealing)
        origin: str = request.headers.get("origin", "").lower()
        referer: str = request.headers.get("referer", "").lower()
        host: str = request.headers.get("host", "").lower()
        
        # Elite SSOT: Authorized Domains - PRODUCTION ONLY
        authorized_domains: Final[list[str]] = ["micsmo.com"]
        
        is_authorized: bool = any(domain in h for domain in authorized_domains for h in [origin, referer, host])
        
        if not is_authorized:
            logger.warning(f"⛔ [Lockdown] Unauthorized domain attempt: host={host}, origin={origin}")
            raise PermissionDeniedException("⛔ Lockdown: Voice service is exclusive to micsmo.com")

        # 2. IP-based Rate Limiting (RAM Protection)
        ip: str = request.client.host if request.client else "unknown"
        now: float = time.time()
        
        if ip not in RATE_LIMIT_STORE:
            RATE_LIMIT_STORE[ip] = []
            
        # Clean old timestamps
        RATE_LIMIT_STORE[ip] = [ts for ts in RATE_LIMIT_STORE[ip] if now - ts < LIMIT_WINDOW]
        
        if len(RATE_LIMIT_STORE[ip]) >= LIMIT_MAX_REQUESTS:
            logger.warning(f"🚨 [Security] Rate limit triggered for IP: {ip}")
            raise TooManyRequestsException("⛔ Lockdown: Rate limit exceeded. Try again in 1 minute.")
            
        RATE_LIMIT_STORE[ip].append(now)

    def _create_tts_stream(self, input_text: str) -> Stream:
        """Helper to create the standardized TTS stream."""
        safe_text: str = input_text[:3000] if input_text else ""
        headers: Final[dict[str, str]] = {
            "Content-Type": "audio/mpeg",
            "Cache-Control": "public, max-age=3600",
            "X-Accel-Buffering": "no",
            "Accept-Ranges": "bytes",
            "Connection": "keep-alive",
            "X-RateLimit-Limit": str(LIMIT_MAX_REQUESTS),
            "X-RateLimit-Remaining": "calculating",
        }
        return Stream(stream_tts_public(safe_text), headers=headers)
