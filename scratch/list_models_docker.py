import asyncio
import os

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
