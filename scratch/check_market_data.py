import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models import ProductBase
import json

async def check():
    async with alchemy_config.create_session_maker()() as session:
        stmt = select(ProductBase).where(ProductBase.id == "prod_miccosmo_virgin_white")
        product = (await session.execute(stmt)).scalar_one_or_none()
        if product:
            print(f"Product: {product.name}")
            print(f"Market Data: {json.dumps(product.market_data, indent=2, ensure_ascii=False)}")
        else:
            print("Product not found")

if __name__ == "__main__":
    asyncio.run(check())
