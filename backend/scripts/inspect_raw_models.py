import asyncio
import httpx
import os
from dotenv import load_dotenv

os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"

async def main():
    from backend.services.ai_engine.core.key_rotator import key_rotator
    await key_rotator.load_keys()
    key = await key_rotator.get_key(model_name="gemini-2.5-flash")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"Total models in API: {len(models)}")
            for m in models:
                if "thinking" in m["name"].lower():
                    print(f"FOUND: {m['name']}")
                    print(m)
        else:
            print(f"Error: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
