import asyncio
import os
from dotenv import load_dotenv

os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/fast_platform"

async def main():
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    from backend.services.ai_engine.core.key_rotator import key_rotator
    
    await key_rotator.load_keys()
    discovered = await trinity_bridge.models_helper.discover_available()
    print("--- ALL DISCOVERED MODELS ---")
    for m in discovered:
        print(m)

if __name__ == "__main__":
    asyncio.run(main())
