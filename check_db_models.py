import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models import VoiceProfile
from sqlalchemy import select

async def check():
    async with alchemy_config.create_session_maker()() as s:
        p = (await s.execute(select(VoiceProfile))).scalar_one_or_none()
        if p:
            print(f"Primary: {p.primary_model}")
            print(f"Waterfall: {p.ai_models}")
        else:
            print("No VoiceProfile found")

if __name__ == "__main__":
    asyncio.run(check())
