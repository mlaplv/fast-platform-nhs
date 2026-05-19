import asyncio
import os
import sys
import json
from dotenv import load_dotenv

project_root = "/home/lv/Desktop/fast-platform-core"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

load_dotenv(os.path.join(project_root, ".env"))

db_url = os.getenv("DATABASE_URL")
if db_url and "@db:" in db_url:
    db_url = db_url.replace("@db:", "@localhost:")
os.environ["DATABASE_URL"] = db_url

# Override Redis host to localhost for host runner
from redis.asyncio import Redis
import backend.services.xohi_memory
backend.services.xohi_memory.xohi_memory.client = Redis.from_url("redis://localhost:6379/0")

from backend.database import async_session_maker, current_tenant_id
from backend.services.commerce.category import category_service

async def test_json():
    async with async_session_maker() as session:
        current_tenant_id.set("default")
        res = await category_service.list_categories(session)
        # Use model_dump to see how Pydantic dumps it (by_alias is determined by Pydantic's model_dump)
        data_default = res.model_dump(mode='json')
        print("--- Root Keys (Default, by_alias=False) ---")
        if data_default["data"]:
            first_cat = data_default["data"][0]
            print(json.dumps(first_cat, indent=2, ensure_ascii=False))

        data_alias = res.model_dump(mode='json', by_alias=True)
        print("\n--- Root Keys (by_alias=True) ---")
        if data_alias["data"]:
            first_cat = data_alias["data"][0]
            print(json.dumps(first_cat, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_json())
