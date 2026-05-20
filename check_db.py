import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform")
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT id, name, price FROM product_bases WHERE name ILIKE '%Miccosmo%' OR name ILIKE '%Serum%' LIMIT 5;"))
        products = result.all()
        print("Products:", products)
        if products:
            p_id = products[0][0]
            v_res = await session.execute(text(f"SELECT id, price, discount_price, attributes FROM product_variants WHERE product_base_id = '{p_id}';"))
            print("Variants:", v_res.all())

asyncio.run(main())
