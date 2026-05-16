import asyncio
from backend.database.session import get_db_session
from backend.database.models.commerce import Order
from sqlalchemy import select

async def main():
    async for db in get_db_session():
        stmt = select(Order).order_by(Order.created_at.desc()).limit(5)
        res = await db.execute(stmt)
        orders = res.scalars().all()
        for o in orders:
            print(f"Order: {o.id}")
            print(f"Total Amount: {o.total_amount}")
            print(f"Status: {o.status}")
            print(f"Metadata: {o.order_metadata}")
            print("-" * 50)
        break

if __name__ == "__main__":
    asyncio.run(main())
