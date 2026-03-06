import asyncio
from src.services.routing.heuristic_classifier import heuristic_classify, COUNT_KEYWORDS
from src.services.routing.stt_corrector import STTCorrector
from src.utils.text import normalize_vn

async def test():
    stt = STTCorrector()
    q = "mở biểu đồ doanh thu"
    
    class DummyState:
        voice_cache = {}
    
    state = DummyState()
    
    cleaned, _ = await stt.correct(q)
    print(f"Norm query: {normalize_vn(cleaned.lower())}")
    
    for kw in COUNT_KEYWORDS:
        if kw in normalize_vn(cleaned.lower()):
            print("Found count keyword:", kw)

asyncio.run(test())
