import os
import time
import logging
from typing import Optional, Final, Dict, List
from litestar import Controller, get, post, Request
from litestar.response import Stream
from litestar.exceptions import PermissionDeniedException, TooManyRequestsException
from pydantic import BaseModel, Field, ConfigDict
from backend.services.client_tts import stream_tts_public

logger = logging.getLogger("api-gateway")

# R5.1: RAM-Safe Rate Limiter (Max 1000 unique IPs in memory)
RATE_LIMIT_STORE: Dict[str, List[float]] = {}
MAX_STORED_IPS: Final[int] = 1000
LIMIT_WINDOW: Final[int] = 60
LIMIT_MAX_REQUESTS: Final[int] = 5

class TTSRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str = Field(..., min_length=1, max_length=3000)

class PublicTTSController(Controller):
    path: Final[str] = "/api/v1/client/tts"

    @get("/stream", sync_to_thread=False)
    async def get_public_tts_stream_get(self, request: Request, text: Optional[str] = None) -> Stream:
        """Standardized TTS GET Entry."""
        self._validate_request(request)
        return self._create_tts_stream(text or "")

    @post("/stream", sync_to_thread=False)
    async def get_public_tts_stream_post(self, request: Request, data: TTSRequest) -> Stream:
        """Standardized TTS POST Entry."""
        self._validate_request(request)
        return self._create_tts_stream(data.text)

    def _validate_request(self, request: Request) -> None:
        """Lockdown Defense V5.1: Security & RAM Guard."""
        # 1. Domain Lockdown
        origin: str = request.headers.get("origin", "").lower()
        referer: str = request.headers.get("referer", "").lower()
        host: str = request.headers.get("host", "").lower()
        
        if not any("micsmo.com" in h for h in [origin, referer, host]):
            raise PermissionDeniedException("⛔ Lockdown: Domain unauthorized.")

        # 2. RAM-Safe Rate Limiting
        ip: str = request.client.host if request.client else "unknown"
        now: float = time.time()
        
        # Prevent Store Overflow (RAM Protection R60.1)
        if len(RATE_LIMIT_STORE) > MAX_STORED_IPS:
            RATE_LIMIT_STORE.clear() # Emergency flush
            
        history: List[float] = RATE_LIMIT_STORE.get(ip, [])
        history = [ts for ts in history if now - ts < LIMIT_WINDOW]
        
        if len(history) >= LIMIT_MAX_REQUESTS:
            logger.warning(f"🚨 [Security] Rate limit: {ip}")
            raise TooManyRequestsException("⛔ Lockdown: Rate limit exceeded.")
            
        history.append(now)
        RATE_LIMIT_STORE[ip] = history

    def _create_tts_stream(self, input_text: str) -> Stream:
        """Elite Stream Factory."""
        headers: Final[dict[str, str]] = {
            "Content-Type": "audio/mpeg",
            "Cache-Control": "public, max-age=3600",
            "X-Accel-Buffering": "no",
            "Accept-Ranges": "bytes",
            "Connection": "keep-alive",
            "X-RateLimit-Limit": str(LIMIT_MAX_REQUESTS),
        }
        return Stream(stream_tts_public(input_text[:3000]), headers=headers)
