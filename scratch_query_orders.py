import asyncio
import json
from backend.database.dependencies import get_session
from backend.database.models.commerce import Order
from sqlalchemy import select

async def main():
    async with get_session() as session:
        stmt = select(Order).where(Order.id.ilike("%4298cedc%"))
        res = await session.execute(stmt)
        orders = res.scalars().all()
        for o in orders:
            print(f"ID: {o.id}")
            print(f"Items: {json.dumps(o.items, indent=2)}")
            print(f"Total: {o.total_amount}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
