
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select
from backend.database import current_tenant_id
from backend.database.session import AsyncSessionLocal
from backend.database.models.commerce import Order

async def check():
    current_tenant_id.set('micsmo-elite')
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Order).where(Order.id == 'a8aab6e9-cb27-420c-a517-1555142d2f09'))
        o = res.scalar_one_or_none()
        if o:
            print(f"ID: {o.id}")
            print(f"Total: {o.total_amount}")
            print(f"Status: {o.status}")
            print(f"Items: {len(o.items) if o.items else 0}")
            print(f"Metadata: {o.order_metadata}")
        else:
            print("Order not found")

if __name__ == "__main__":
    asyncio.run(check())
