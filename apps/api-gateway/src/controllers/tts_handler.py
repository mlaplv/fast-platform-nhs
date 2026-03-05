from litestar import Controller, get
from litestar.response import Stream
from src.services.tts_engine import stream_tts

class TTSController(Controller):
    path = "/api/v1/tts"

    @get("/stream")
    async def get_tts_stream(self, text: str) -> Stream:
        """Endpoint to stream TTS audio to the frontend."""
        return Stream(stream_tts(text), media_type="audio/mpeg")
