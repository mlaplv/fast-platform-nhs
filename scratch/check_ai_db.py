import asyncio
import json
import os
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models import SystemSetting, VoiceProfile

async def check():
    print(f"DATABASE URL: {os.getenv('REDIS_URL', 'Not Set')}") # Checking env for clues
    
    async with alchemy_config.create_session_maker()() as session:
        try:
            # Check Orchestration Config
            setting = (await session.execute(
                select(SystemSetting).where(SystemSetting.key == "ai_orchestration_config")
            )).scalar_one_or_none()
            
            print(f"--- AI ORCHESTRATION CONFIG (SystemSetting) ---")
            if setting:
                print(json.dumps(setting.value, indent=2))
            else:
                print("NOT FOUND (Using hardcoded defaults in trinity_models.py)")
        except Exception as e:
            print(f"Error reading system_settings: {e}")

        try:
            # Check Voice Profile (Waterfalls)
            profile = (await session.execute(
                select(VoiceProfile)
            )).scalars().first()
            
            print(f"\n--- VOICE PROFILE (First User) ---")
            if profile:
                print(f"User ID: {profile.user_id}")
                print(f"Primary Model: {profile.primary_model}")
                print(f"Waterfall: {profile.ai_models}")
                print(f"Discovered: {len(profile.discovered_models if profile.discovered_models else [])} models")
            else:
                print("NO VOICE PROFILES FOUND")
        except Exception as e:
            print(f"Error reading voice_profiles: {e}")

if __name__ == "__main__":
    asyncio.run(check())
