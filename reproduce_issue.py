import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.commerce.logic.lead_extractor import LeadExtractor
from unittest.mock import AsyncMock

async def test_reproduce_loop():
    # Setup
    extractor = LeadExtractor()
    message = "2 lọ"
    # Assume db is not needed for the extraction part if we mock the agent?
    # Actually, the agent is called at line 156.
    # Let's see if we can just test the extractor with a real agent call or mock it.
    # The error seems to be that items are empty.

    # I'll just check what LeadExtractor returns for "2 lọ".
    # Need to mock trinity_bridge
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    trinity_bridge.run = AsyncMock(return_value={"is_definite_purchase": False, "items": []})

    db = AsyncMock(spec=AsyncSession)

    result = await extractor.extract_and_convert(db, message, "session_test")
    print(f"Result: is_definite_purchase={result.is_definite_purchase}, items={result.items}")

if __name__ == "__main__":
    asyncio.run(test_reproduce_loop())
