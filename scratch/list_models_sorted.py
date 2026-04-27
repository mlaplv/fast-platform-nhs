import asyncio
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.ai_engine.core.trinity_models import TrinityModels

async def check():
    models_helper = TrinityModels(key_rotator, "gemini-1.5-flash", "gemini-1.5-flash")
    discovered = await models_helper.discover_available()
    
    for role in ["brain", "fast"]:
        models = models_helper.get_role_models(role, discovered)
        print(f"\nRole [{role.upper()}] Models (Sorted):")
        for m in models:
            score = models_helper._score_model(m)
            print(f" - {m} (Score: {score})")

if __name__ == "__main__":
    asyncio.run(check())
