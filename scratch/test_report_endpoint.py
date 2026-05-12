import asyncio
import httpx
import json

async def test_generate_report():
    url = "http://localhost:8000/api/v1/ads-protection/generate-investigation-report"
    payload = {
        "date_from": "2026-05-01",
        "date_to": "2026-05-12"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=30.0)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_generate_report())
