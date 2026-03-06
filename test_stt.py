import asyncio
from src.services.routing.stt_corrector import STTCorrector

async def test():
    stt = STTCorrector()
    print(await stt.correct("số tháng này bao nhiêu"))
    print(await stt.correct("dân số"))
    print(await stt.correct("dân số bao nhiêu"))
asyncio.run(test())
