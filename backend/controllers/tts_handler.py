from litestar import Controller, get, post
from litestar.response import Stream
from pydantic import BaseModel, Field
from backend.services.tts_engine import stream_tts
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)

class TTSController(Controller):
    path = "/api/v1/tts"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    def _create_stream(self, text: str) -> Stream:
        """Shared logic for both GET and POST streaming."""
        headers = {
            "Content-Type": "audio/mpeg",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        }
        return Stream(stream_tts(text), headers=headers)

    @get("/stream")
    async def get_tts_stream(self, text: str) -> Stream:
        """Endpoint to stream TTS audio via GET."""
        return self._create_stream(text)

    @post("/stream")
    async def post_tts_stream(self, data: TTSRequest) -> Stream:
        """Endpoint to stream TTS audio via POST (Fix 405)."""
        return self._create_stream(data.text)
