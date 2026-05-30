import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # 1. Gọi thử public health check xem API có chạy không
        try:
            res = await client.get("http://localhost:8000/health")
            print(f"Health check status: {res.status_code}")
        except Exception as e:
            print(f"Cannot connect to API: {e}")
            return

        # 2. Gọi thử share-intent
        res = await client.post("http://localhost:8000/api/v1/client/viral/share-intent", json={"product_id": "test-product"})
        print(f"Share intent status: {res.status_code}, content: {res.text}")

        # 3. Gọi thử oauth-gateway
        res = await client.get("http://localhost:8000/api/v1/client/viral/oauth-gateway?state=test&platform=facebook&product_id=test-product")
        print(f"OAuth gateway status: {res.status_code}")

if __name__ == "__main__":
    asyncio.run(test())
