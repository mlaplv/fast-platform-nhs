import asyncio
import logging
import sys

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        from backend.database.alchemy_config import alchemy_config
        from backend.database.models import VoiceProfile, User
        from sqlalchemy import select
        
        maker = alchemy_config.create_session_maker()
        async with maker() as s:
            profiles = (await s.execute(select(VoiceProfile))).scalars().all()
            print(f"=== ALL VOICE PROFILES WITH USER TENANT ===")
            for p in profiles:
                u = (await s.execute(select(User).where(User.id == p.user_id))).scalar_one_or_none()
                if u:
                    print(f"User: {u.email} | Tenant ID: {u.tenant_id} | Primary: {p.primary_model} | Waterfall: {p.ai_models}")
                else:
                    print(f"Profile ID: {p.id} | User ID: {p.user_id} (User not found!)")
    except Exception as e:
        print(f"Error querying VoiceProfile: {e}")

if __name__ == "__main__":
    asyncio.run(main())
