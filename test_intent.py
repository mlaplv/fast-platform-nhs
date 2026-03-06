import asyncio
from src.services.routing.heuristic_classifier import heuristic_classify
from src.services.routing.stt_corrector import STTCorrector
from src.utils.text import normalize_vn

async def run():
    stt = STTCorrector()
    transcript = "số tháng này bao nhiêu"
    cleaned, _ = await stt.correct(transcript)
    print("STT Corrector output:", cleaned)
    
    class DummyState:
        voice_cache = {}
        
    state = DummyState()
    res = heuristic_classify(cleaned.lower(), "admin123", state)
    print("Intent:", res)

asyncio.run(run())
