import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services.commerce.product import ProductService
from backend.services.commerce.product_vector import ProductVectorService

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"

async def test_direct_query():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Setup service
    vector_service = ProductVectorService()
    product_service = ProductService(vector_service=vector_service)
    
    async with async_session() as session:
        print("=== QUERYING 'White Label' DIRECTLY via SERVICE ===")
        res = await product_service.list_products(session, brand="White Label")
        print(f"Products returned count: {res.total} (len={len(res.data)})")
        for p in res.data:
            print(f"- {p.name} | brand: {p.attributes.get('brand')} | Thương hiệu: {p.attributes.get('Thương hiệu')}")

        print("\n=== QUERYING 'White+Label' DIRECTLY via SERVICE ===")
        res2 = await product_service.list_products(session, brand="White+Label")
        print(f"Products returned count: {res2.total} (len={len(res2.data)})")
        for p in res2.data:
            print(f"- {p.name} | brand: {p.attributes.get('brand')} | Thương hiệu: {p.attributes.get('Thương hiệu')}")

if __name__ == "__main__":
    asyncio.run(test_direct_query())
