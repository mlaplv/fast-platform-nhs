import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=120) as c:
        print("Sending POST request...")
        r = await c.post("http://localhost:8000/api/v1/content/scout", json={"topic": "Dịch vụ giặt ghế sofa"})
        print(r.status_code, r.text)

asyncio.run(main())
