import asyncio
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.ai_engine.core.trinity_models import TrinityModels

async def check():
    models_helper = TrinityModels(key_rotator, "gemini-1.5-flash", "gemini-1.5-flash")
    discovered = await models_helper.discover_available()
    print(f"Discovered {len(discovered)} models:")
    for m in discovered:
        print(f" - {m}")
    
    brain_models = models_helper.get_role_models("brain", discovered)
    print(f"\nBrain Role Models: {brain_models}")

if __name__ == "__main__":
    asyncio.run(check())
