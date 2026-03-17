from litestar import Controller, get
from litestar.response import Stream
from backend.services.voice_service import voice_service

class TTSController(Controller):
    path = "/api/v1/tts"

    @get("/stream")
    async def get_tts_stream(self, text: str) -> Stream:
        """Endpoint to stream TTS audio to the frontend."""
        return Stream(voice_service.stream_tts(text), media_type="audio/mpeg")
