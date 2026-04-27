import asyncio
import os
from backend.services.ai_engine.core.key_rotator import key_rotator
import json
import time

async def run():
    await key_rotator.load_keys()
    keys = key_rotator.keys
    print(f"Total keys loaded: {len(keys)}")
    
    if not key_rotator.client:
        print("❌ Redis client not connected.")
        return

    now = time.time()
    for i, key in enumerate(keys):
        kid = key_rotator._get_key_id(key)
        
        # Check blacklist
        is_bl = await key_rotator.client.exists(f"{key_rotator.BLACKLIST_PREFIX}{kid}")
        # Check global health
        meta = await key_rotator.client.hgetall(f"{key_rotator.METADATA_PREFIX}{kid}")
        
        # Check specific models cooldown
        models_check = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-pro", "gemini-2.0-flash"]
        cooldowns = []
        for m in models_check:
            m_key = f"{key_rotator.MODEL_DAILY_PREFIX}{kid}:{m.replace('/', '_').replace('-', '_')[:40]}"
            if await key_rotator.client.exists(m_key):
                cooldowns.append(m)
        
        status = "❌ BLACKLISTED" if is_bl else "✅ OK"
        health = meta.get("health_score", "100")
        fail_count = meta.get("fail_count", "0")
        
        print(f"Key {i+1} ({key[:8]}...): {status} | Health: {health} | Fails: {fail_count}")
        if cooldowns:
            print(f"   └─ Exhausted for: {', '.join(cooldowns)}")

if __name__ == "__main__":
    asyncio.run(run())
