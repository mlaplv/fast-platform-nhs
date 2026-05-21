import asyncio
import sys
import os

sys.path.append("/app")
sys.path.append("/home/lv/Desktop/fast-platform-core")

os.environ["DB_HOST"] = "localhost"

from backend.database.alchemy_config import alchemy_config
from backend.database.models import VoiceProfile
from sqlalchemy import select

async def main():
    async with alchemy_config.create_session_maker()() as session:
        profiles = (await session.execute(select(VoiceProfile))).scalars().all()
        print(f"Total VoiceProfiles found: {len(profiles)}")
        for idx, p in enumerate(profiles):
            print(f"\nProfile #{idx+1}:")
            print(f"  - User ID: {p.user_id}")
            print(f"  - Primary Model: {p.primary_model}")
            print(f"  - AI Models (Waterfall): {p.ai_models}")
            print(f"  - Status: {p.status}")

if __name__ == "__main__":
    asyncio.run(main())
