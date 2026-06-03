import asyncio
from dotenv import load_dotenv
load_dotenv("/home/lv/Desktop/fast-platform-core/.env")

from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.commerce import ProductBase

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        stmt = select(ProductBase.name, ProductBase.slug)
        res = await db.execute(stmt)
        rows = res.all()
        print(f"TOTAL PRODUCTS: {len(rows)}")
        for i, row in enumerate(rows):
            print(f"{i+1}. NAME: {row.name} | SLUG: {row.slug}")

if __name__ == "__main__":
    asyncio.run(main())
