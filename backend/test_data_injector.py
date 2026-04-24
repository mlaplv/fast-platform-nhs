import asyncio
import logging
import sys

from backend.database.session import SessionLocal
from backend.database.repositories import OrderRepository
from backend.services.data_injector import data_injector

logging.basicConfig(level=logging.DEBUG)

async def test_fetch():
    async with SessionLocal() as session:
        repo = OrderRepository(session)
        res = await data_injector._fetch_revenue_series(order_repo=repo)
        print("RESULT:")
        print(res)

if __name__ == "__main__":
    asyncio.run(test_fetch())
