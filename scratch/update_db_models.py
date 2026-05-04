import os
import sys
import asyncio
from sqlalchemy import update

# Add project root to sys.path
sys.path.append(os.getcwd())

# Load .env manually
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key] = value.strip("'").strip('"')

load_env()

# CRITICAL: Set DATABASE_URL to use localhost
if "DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].replace("@db:", "@localhost:")

async def update_db():
    from backend.database.alchemy_config import alchemy_config
    from backend.database.models import VoiceProfile

    async with alchemy_config.create_session_maker()() as session:
        # Update primary_model and remove 1.5-flash from ai_models
        from sqlalchemy import select
        result = await session.execute(select(VoiceProfile))
        profiles = result.scalars().all()
        
        for p in profiles:
            print(f"Updating profile for user: {p.user_id}")
            p.primary_model = "gemini-2.5-flash"
            if p.ai_models:
                p.ai_models = [m for m in p.ai_models if m != "gemini-1.5-flash"]
            session.add(p)
        
        await session.commit()
        print("Successfully updated all voice profiles.")

if __name__ == "__main__":
    asyncio.run(update_db())
