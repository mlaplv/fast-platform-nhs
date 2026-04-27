import asyncio
import os
import httpx
from backend.services.ai_engine.core.key_rotator import key_rotator

async def run():
    await key_rotator.load_keys()
    keys = key_rotator.keys
    print(f"Testing {len(keys)} keys with gemini-1.5-flash...")
    
    for i, key in enumerate(keys):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
        payload = {"contents": [{"parts": [{"text": "hi"}]}]}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    print(f"Key {i+1}: ✅ OK")
                else:
                    print(f"Key {i+1}: ❌ {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"Key {i+1}: 🚨 {e}")

if __name__ == "__main__":
    asyncio.run(run())
