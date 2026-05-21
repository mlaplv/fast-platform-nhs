import asyncio
import sys
import os
import json
import httpx

sys.path.append("/app")
sys.path.append("/home/lv/Desktop/fast-platform-core")

os.environ["DB_HOST"] = "localhost"

from backend.services.ai_engine.core.key_rotator import key_rotator

async def test_key_model(key: str, model: str) -> tuple[bool, str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Say OK"}]}]
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                return True, text
            else:
                return False, f"HTTP {resp.status_code} - {resp.json().get('error', {}).get('message', '')[:100]}"
    except Exception as e:
        return False, str(e)

async def main():
    await key_rotator.load_keys()
    models_to_test = [
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite"
    ]
    
    print("=== MULTI-MODEL CONNECTIVITY TEST ===")
    for model in models_to_test:
        print(f"\n--- Testing Model: {model} ---")
        success_count = 0
        for idx, key in enumerate(key_rotator.keys[:3]):  # Test first 3 keys for speed
            ok, res = await test_key_model(key, model)
            masked = key[:8] + "..."
            print(f"  Key #{idx+1} ({masked}): {'✅ SUCCESS' if ok else '❌ FAILED'} -> {res}")
            if ok:
                success_count += 1
        print(f"-> Model {model} has {success_count}/3 keys working.")

if __name__ == "__main__":
    asyncio.run(main())
