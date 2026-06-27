import asyncio
import os
import sys
import json
import hashlib
import httpx

# Load .env file
def load_env():
    env_path = "/media/lv/data/fast-platform-core/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        os.environ[key] = val

load_env()

def _get_key_id(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

async def test_key(key: str):
    kid = _get_key_id(key)
    models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-pro"]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        results = []
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": "say hi"}]}]}
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    results.append(f"{model}: ✅ OK")
                else:
                    try:
                        err_msg = resp.json().get("error", {}).get("message", "")
                    except:
                        err_msg = resp.text
                    results.append(f"{model}: ❌ {resp.status_code} ({err_msg[:50]})")
            except Exception as e:
                results.append(f"{model}: ❌ ERROR ({e})")
        print(f"Key {key[:8]}... (hash: {kid}): {', '.join(results)}")

async def main():
    support_keys_raw = os.getenv("SUPPORT_GEMINI_KEYS")
    if not support_keys_raw:
        print("No SUPPORT_GEMINI_KEYS found!")
        return
        
    support_keys_raw = support_keys_raw.strip()
    if (support_keys_raw.startswith("'") and support_keys_raw.endswith("'")) or (support_keys_raw.startswith('"') and support_keys_raw.endswith('"')):
        support_keys_raw = support_keys_raw[1:-1].strip()
        
    keys = json.loads(support_keys_raw)
    print(f"Testing {len(keys)} keys...")
    
    tasks = [test_key(k) for k in keys]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
