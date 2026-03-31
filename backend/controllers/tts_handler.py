from litestar import Controller, get
from litestar.response import Stream
from backend.services.tts_engine import stream_tts
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

class TTSController(Controller):
    path = "/api/v1/tts"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    @get("/stream")
    async def get_tts_stream(self, text: str) -> Stream:
        """Endpoint to stream TTS audio (Standardized V2.2)."""
        headers = {
            "Content-Type": "audio/mpeg",
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        }
        return Stream(stream_tts(text), headers=headers)
