import asyncio
import os
import sys

# Add workspace to path
sys.path.append("/app")

from backend.database.alchemy_config import alchemy_config
from backend.database.models import VoiceProfile
from sqlalchemy import select

async def run():
    async with alchemy_config.create_session_maker()() as s:
        p = (await s.execute(select(VoiceProfile))).scalars().first()
        if p:
            print(f"DB_PRIMARY: {p.primary_model}")
            print(f"DB_WATERFALL: {p.ai_models}")
        else:
            print("No VoiceProfile found")

if __name__ == "__main__":
    asyncio.run(run())
