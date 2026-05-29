import asyncio
import sys
import os
import json
import httpx

# Load .env
def load_env():
    env_path = "/home/lv/Desktop/fast-platform-core/.env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ[k] = v

load_env()

# Modify DATABASE_URL if db host is not resolvable to localhost
db_url = os.environ.get("DATABASE_URL")
if db_url and "@db:" in db_url:
    import socket
    try:
        socket.gethostbyname("db")
    except socket.gaierror:
        os.environ["DATABASE_URL"] = db_url.replace("@db:", "@localhost:")

from backend.services.ai_engine.core.key_rotator import key_rotator

async def test_key_model(key: str, model: str) -> tuple[bool, str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Say OK"}]}]
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
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
    models = ["gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-1.5-pro", "gemini-2.0-flash"]
    print("=== TESTING VARIOUS MODELS AGAINST ALL 8 KEYS ===")
    for model in models:
        print(f"\n--- Testing {model} ---")
        for idx, key in enumerate(key_rotator.keys):
            ok, res = await test_key_model(key, model)
            masked = key[:8] + "..." + key[-4:]
            print(f"  Key #{idx+1} ({masked}): {'✅ SUCCESS' if ok else '❌ FAILED'} -> {res}")
            if ok:
                print(f"🎉 FOUND WORKING KEY FOR {model}: {masked}")

if __name__ == "__main__":
    asyncio.run(main())
