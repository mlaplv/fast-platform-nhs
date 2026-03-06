import asyncio
from src.services.routing.heuristic_classifier import heuristic_classify
from src.services.routing.stt_corrector import STTCorrector
from src.utils.text import normalize_vn

async def test():
    stt = STTCorrector()
    queries = [
        "số tháng này bao nhiêu",
        "dân số",
        "mở biểu đồ doanh thu"
    ]
    
    class DummyState:
        voice_cache = {}
    
    state = DummyState()
    
    for q in queries:
        cleaned, _ = await stt.correct(q)
        print(f"--- Query: '{q}' -> Cleaned: '{cleaned}' ---")
        res = heuristic_classify(cleaned.lower(), "admin123", state)
        if res:
             print(f"Action: {res.action}, Intent: {res.data.get('intent_type')}")
        else:
             print("Action: None (Falls to T2)")

asyncio.run(test())
