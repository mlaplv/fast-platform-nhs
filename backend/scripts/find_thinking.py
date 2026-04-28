import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv(".env")

async def main():
    key = os.getenv("GEMINI_API_KEY") # Or I can try to find another key if this fails
    if not key:
        print("No API key found in .env")
        return
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            for m in models:
                name = m.get("name", "")
                if "thinking" in name.lower() or "flash" in name.lower():
                    print(f"Name: {name}")
                    print(f"Methods: {m.get('supportedGenerationMethods')}")
                    print("-" * 20)
        else:
            print(f"Error: {resp.status_code}")
            print(resp.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
