import asyncio
import redis.asyncio as aioredis
import os

PRODUCT_ID = "prod_miccosmo_virgin_white"

async def main():
    r = aioredis.Redis(host="localhost", port=6379, db=0)
    # Scan all keys starting with viral:
    keys = await r.keys("viral:*")
    print(f"Active viral keys in Redis: {keys}")
    for k in keys:
        val = await r.get(k)
        ttl = await r.ttl(k)
        print(f"Key: {k.decode()} | Value: {val.decode() if val else 'None'} | TTL: {ttl}s")
    await r.close()

if __name__ == "__main__":
    asyncio.run(main())
