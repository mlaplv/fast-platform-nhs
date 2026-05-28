import asyncio
import os
import sys

# Add backend to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.xohi_memory import xohi_memory

async def main():
    print(f"xohi_memory._use_redis: {xohi_memory._use_redis}")
    if xohi_memory.client:
        try:
            val = await xohi_memory.client.get("config:shipping:default_fee")
            print(f"Value in Redis for 'config:shipping:default_fee': {val}")
        except Exception as e:
            print(f"Error getting value from Redis: {e}")
    else:
        print("Redis client is None!")

if __name__ == "__main__":
    asyncio.run(main())
