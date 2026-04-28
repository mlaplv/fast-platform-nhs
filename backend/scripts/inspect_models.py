import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv(".env")

async def main():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        print("No API key found.")
        return
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            # Print the first few to see schema
            for m in models[:10]:
                print(json.dumps(m, indent=2))
        else:
            print(f"Error: {resp.status_code}")
            print(resp.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
