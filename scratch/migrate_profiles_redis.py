import asyncio
import sys
import os

sys.path.append("/app")
sys.path.append("/home/lv/Desktop/fast-platform-core")

os.environ["DB_HOST"] = "localhost"

from backend.database.alchemy_config import alchemy_config
from backend.database.models import VoiceProfile
from backend.services.ai_engine.core.key_rotator import key_rotator
from sqlalchemy import select

async def main():
    print("🚀 Updating VoiceProfiles in DB to latest 2026 models...")
    async with alchemy_config.create_session_maker()() as session:
        profiles = (await session.execute(select(VoiceProfile))).scalars().all()
        for p in profiles:
            print(f"Updating profile for User: {p.user_id}")
            p.primary_model = "gemini-3.5-flash"
            p.ai_models = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
            session.add(p)
        await session.commit()
    print("✅ DB Update completed.")

    print("\n🧹 Clearing false-positive daily limits and unhealthy states from Redis...")
    if key_rotator._use_redis and key_rotator.client is not None:
        client = key_rotator.client
        # Find all keys in Redis related to key statuses
        keys_to_del = []
        
        # 1. Clear key blacklists
        black_keys = await client.keys(f"{key_rotator.BLACKLIST_PREFIX}*")
        keys_to_del.extend(black_keys)
        
        # 2. Clear key daily exhaustion records
        daily_keys = await client.keys(f"{key_rotator.MODEL_DAILY_PREFIX}*")
        keys_to_del.extend(daily_keys)
        
        # 3. Clear key metadata (resets fail_count & health_score)
        meta_keys = await client.keys(f"{key_rotator.METADATA_PREFIX}*")
        keys_to_del.extend(meta_keys)
        
        # 4. Clear model poisons
        poison_keys = await client.keys(f"{key_rotator.POISON_PREFIX}*")
        keys_to_del.extend(poison_keys)
        
        if keys_to_del:
            print(f"Found {len(keys_to_del)} status keys to delete in Redis.")
            await client.delete(*keys_to_del)
            print("✅ Redis states successfully reset.")
        else:
            print("No status keys found in Redis.")
    else:
        print("Redis client not active.")

if __name__ == "__main__":
    asyncio.run(main())
