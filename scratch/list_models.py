import asyncio
import os
import sys

# Add workspace to path
sys.path.append("/app")

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

async def run():
    models = await trinity_bridge.models_helper.discover_available()
    print(f"Total discovered: {len(models)}")
    print(f"Models: {models}")

if __name__ == "__main__":
    asyncio.run(run())
