import asyncio
import logging
import sys
import os
from sqlalchemy import select

# Load .env file manually
def load_env():
    env_path = "/media/lv/data/fast-platform-core/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        os.environ[key] = val

load_env()

sys.path.append("/media/lv/data/fast-platform-core")

from backend.database.alchemy_config import alchemy_config
from backend.database.models.auth import VoiceProfile, User

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        # Query Users
        users = (await session.execute(
            select(User)
        )).scalars().all()
        print("--- USERS ---")
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, TenantID: {u.tenant_id}")

        # Query VoiceProfiles
        profiles = (await session.execute(
            select(VoiceProfile)
        )).scalars().all()
        print("\n--- VOICE PROFILES ---")
        for p in profiles:
            print(f"ID: {p.id}, UserID: {p.user_id}, PrimaryModel: {p.primary_model}, AIModels: {p.ai_models}")

if __name__ == "__main__":
    asyncio.run(main())
