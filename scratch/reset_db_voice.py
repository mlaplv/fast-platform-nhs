import asyncio
import os
import sys

# Add workspace to path
sys.path.append("/app")

from backend.database.alchemy_config import alchemy_config
from backend.database.models import VoiceProfile
from sqlalchemy import update

async def run():
    async with alchemy_config.create_session_maker()() as s:
        # Reset all VoiceProfiles to dynamic routing (models = null)
        await s.execute(
            update(VoiceProfile).values(
                primary_model=None,
                ai_models=None
            )
        )
        await s.commit()
        print("✅ Database VoiceProfile reset to Dynamic Routing (NULL).")

if __name__ == "__main__":
    asyncio.run(run())
