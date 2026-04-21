import asyncio
from backend.services.commerce.logic.lead_extractor import lead_extractor
from backend.database.alchemy_config import alchemy_config
async def test():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        try:
            lead = await lead_extractor.extract_and_convert(db, "cho 1 kem trị mụn về 123 nguyễn huệ, q1. sđt 0988772211", "test-session-3")
            print("LEAD:", lead)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
