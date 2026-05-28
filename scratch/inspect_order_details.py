import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import Order

async def inspect():
    async with async_session_maker() as db_session:
        ord_stmt = select(Order).where(Order.id.like("bd6bd0e1%"))
        ord_res = await db_session.execute(ord_stmt)
        o = ord_res.scalar_one_or_none()
        if o:
            print(f"Total: {o.total_amount}")
            print(f"Metadata: {o.order_metadata}")
            print(f"Shipping Fee: {o.order_metadata.get('shipping_fee') if o.order_metadata else 'None'}")
            print(f"Items: {o.order_metadata.get('items') if o.order_metadata else 'None'}")

if __name__ == "__main__":
    asyncio.run(inspect())
