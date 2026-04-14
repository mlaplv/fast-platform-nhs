import asyncio
from sqlalchemy import select
from backend.database import session_factory
from backend.database.models.commerce import Order
import json

async def check_order(order_id: str):
    async with session_factory() as session:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()
        
        if not order:
            print(f"Order {order_id} not found.")
            return
            
        print(f"Order ID: {order.id}")
        print(f"Customer: {order.customer_name} ({order.customer_phone})")
        print(f"Items: {json.dumps(order.items, indent=2)}")
        print(f"Metadata: {json.dumps(order.order_metadata, indent=2)}")

if __name__ == "__main__":
    order_id = "7d553374-337c-4469-9450-309871409bf4"
    asyncio.run(check_order(order_id))
