import asyncio
from src.services.routing.heuristic_classifier import heuristic_classify
from src.services.routing.stt_corrector import STTCorrector

async def test():
    stt = STTCorrector()
    q1 = "số tháng này bao nhiêu"
    q2 = "dân số"
    q3 = "mở biểu đồ doanh thu"
    
    class DummyState:
        voice_cache = {}
    
    state = DummyState()
    
    for q in [q1, q2, q3]:
        cleaned, _ = await stt.correct(q)
        print(f"--- Query: '{q}' -> Cleaned: '{cleaned}' ---")
        res = heuristic_classify(cleaned.lower(), "admin123", state)
        if res:
             print(f"Action: {res.action}, Intent: {res.data.get('intent_type')}")
        else:
             print("Action: None (Falls to T2)")

asyncio.run(test())
