import os
import sys
import asyncio
import json

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

# CRITICAL: Set DATABASE_URL to use localhost BEFORE importing alchemy_config
if "DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].replace("@db:", "@localhost:")

async def check_db_keys():
    from backend.database.alchemy_config import alchemy_config
    from backend.database.models import VoiceProfile
    from backend.utils.security import GeminiSecurity
    from sqlalchemy import select

    async with alchemy_config.create_session_maker()() as session:
        result = await session.execute(select(VoiceProfile).where(VoiceProfile.gemini_keys_enc != None))
        rows = result.scalars().all()

        print(f"Found {len(rows)} profiles with keys.")
        for profile in rows:
            print(f"User: {profile.user_id}")
            # Use the actual project decryption
            decrypted = GeminiSecurity.decrypt(profile.gemini_keys_enc)
            
            if isinstance(decrypted, list):
                print(f"  Keys count: {len(decrypted)}")
            elif isinstance(decrypted, str):
                print(f"  Decrypted is STRING of length: {len(decrypted)}")
                print(f"  First 16 chars: {decrypted[:16]}")
            else:
                print(f"  Other type: {type(decrypted)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_db_keys())
