import asyncio
import os
import sys
import json
import logging

# Add backend to path
sys.path.append("/app")
sys.path.append("/home/lv/Desktop/fast-platform-core")

os.environ["DB_HOST"] = "localhost"  # run on host

from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.database.alchemy_config import alchemy_config
from backend.database.models import VoiceProfile
from backend.utils.security import GeminiSecurity
from sqlalchemy import select
import httpx

async def test_key(key: str, model: str = "gemini-2.0-flash") -> tuple[bool, str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Hello, answer in 1 word."}]}]
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return True, resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                return False, f"HTTP {resp.status_code} - {resp.text}"
    except Exception as e:
        return False, str(e)

async def main():
    await key_rotator.load_keys()
    print("==================================================")
    print(f"LOADED KEYS COUNT: {len(key_rotator.keys)}")
    print("==================================================")
    
    if not key_rotator.keys:
        print("No keys loaded.")
        return

    # Check key status in Redis
    use_redis = key_rotator._use_redis and key_rotator.client is not None
    print(f"Using Redis: {use_redis}")
    
    for idx, key in enumerate(key_rotator.keys):
        kid = key_rotator._get_key_id(key)
        masked_key = key[:8] + "..." + key[-8:] if len(key) > 16 else key
        print(f"\nKey #{idx+1}: {masked_key} (ID: {kid})")
        
        if use_redis:
            is_blacklisted = await key_rotator.client.exists(f"{key_rotator.BLACKLIST_PREFIX}{kid}")
            meta = await key_rotator.client.hgetall(f"{key_rotator.METADATA_PREFIX}{kid}")
            
            # Check daily exhaustion for gemini-2.0-flash
            model_daily_flash = await key_rotator.client.exists(f"{key_rotator.MODEL_DAILY_PREFIX}{kid}:gemini_2.0_flash")
            model_daily_lite = await key_rotator.client.exists(f"{key_rotator.MODEL_DAILY_PREFIX}{kid}:gemini_2.5_flash_lite")
            
            print(f"  - Blacklisted: {is_blacklisted}")
            print(f"  - Meta: {meta}")
            print(f"  - Daily Exhausted (gemini-2.0-flash): {bool(model_daily_flash)}")
            print(f"  - Daily Exhausted (gemini-2.5-flash-lite): {bool(model_daily_lite)}")
        
        # Test key connectivity
        ok, res = await test_key(key, "gemini-2.0-flash")
        print(f"  - Test gemini-2.0-flash: {'SUCCESS' if ok else 'FAILED'} -> {res}")
        
        ok_lite, res_lite = await test_key(key, "gemini-2.5-flash-lite")
        print(f"  - Test gemini-2.5-flash-lite: {'SUCCESS' if ok_lite else 'FAILED'} -> {res_lite}")

if __name__ == "__main__":
    asyncio.run(main())
