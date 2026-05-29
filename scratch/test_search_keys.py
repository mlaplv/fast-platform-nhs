import asyncio
import json
import httpx

keys = ["AIzaSyCyMT4rGfXOLAb_7w6szxEICAadSv2zc2o", "AIzaSyDOKHL3s1gczXTNnGttbSqGIhH8VcHAEAE", "AIzaSyD-5jkIOU9lLzRck0pmh2-Nmod6uRJaA7A"]

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
    print("=== TESTING GOOGLE SEARCH KEYS FOR GEMINI ===")
    for idx, key in enumerate(keys):
        ok, res = await test_key_model(key, "gemini-2.0-flash")
        print(f"Search Key #{idx+1}: {'✅ SUCCESS' if ok else '❌ FAILED'} -> {res}")

if __name__ == "__main__":
    asyncio.run(main())
