import asyncio
import os
from backend.services.ai_engine.core.key_rotator import key_rotator
import json

async def run():
    await key_rotator.load_keys()
    # Mocking redis if needed or assuming it's connected
    # Actually key_rotator uses Redis internally.
    keys = key_rotator._keys
    print(f"Total keys loaded: {len(keys)}")
    
    # Check health/poison state
    for i, key in enumerate(keys):
        is_healthy = await key_rotator.is_healthy(key)
        print(f"Key {i+1}: {'✅ HEALTHY' if is_healthy else '❌ UNHEALTHY'}")

if __name__ == "__main__":
    asyncio.run(run())
