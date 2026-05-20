import asyncio
import os
import json
from dotenv import load_dotenv

# Load workspace .env
load_dotenv("/home/lv/Desktop/fast-platform-core/.env")

# Override db host to 127.0.0.1 for host-side execution
db_url = os.environ.get("DATABASE_URL")
if db_url and "@db:" in db_url:
    os.environ["DATABASE_URL"] = db_url.replace("@db:", "@127.0.0.1:")

from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models.commerce import Order

async def inspect_order():
    async with async_session_maker() as session:
        stmt_order = select(Order).where(Order.id == "5464b1da-4196-4302-b7a1-69351ff7319b")
        res_order = await session.execute(stmt_order)
        order = res_order.scalar_one_or_none()
        
        if order:
            print("=== ORDER ID:", order.id)
            print("Total Amount:", order.total_amount)
            print("Order Metadata:", json.dumps(order.order_metadata, indent=2))
            print("Points Earned:", order.points_earned)
            print("Points Redeemed:", order.points_redeemed)
            print("Point Discount Amount:", order.point_discount_amount)
            print("Items List:", json.dumps(order.items, indent=2))
        else:
            print("Order not found.")

if __name__ == "__main__":
    asyncio.run(inspect_order())
