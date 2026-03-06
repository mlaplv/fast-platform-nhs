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
    norm_query = normalize_vn(cleaned.lower())
    
    is_nav_explicit = any(kw in norm_query for kw in ["bieu do", "mo ", "xem "])
    target = "revenue"
    print("is_nav_explicit:", is_nav_explicit)
    print("target == 'revenue' and not is_nav_explicit:", (target == 'revenue' and not is_nav_explicit))
    
    res = heuristic_classify(cleaned.lower(), "admin123", state)
    print("Result:", res.data.get("intent_type"))

asyncio.run(test())
