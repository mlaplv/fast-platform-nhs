import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(follow_redirects=True, verify=False, timeout=60.0) as client:
        # Targeting the local instance for direct debug logs
        print("Sending request to https://api.osmo.vn/api/v1/articles...")
        try:
            res = await client.post('https://api.osmo.vn/api/v1/articles', json={
                "title": "Test Title Neural Sync " + str(asyncio.get_event_loop().time()),
                "category": "Bài viết",
                "status": "DRAFT",
                "content": "<p>Nội dung thử nghiệm Auto-Leach.</p>",
                "metadata": {"faqs": []}
            })
            print("Status:", res.status_code)
            print("Body:", res.text)
        except Exception as e:
            print("Request failed:", e)

asyncio.run(main())
