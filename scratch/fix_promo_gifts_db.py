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
from backend.database.models.commerce import ProductVariant, Order

async def fix_database():
    async with async_session_maker() as session:
        # 1. Update Variant v_ea1b5d6f82ea attributes to contain the promotional gift
        stmt_variant = select(ProductVariant).where(ProductVariant.id == "v_ea1b5d6f82ea")
        res_variant = await session.execute(stmt_variant)
        variant = res_variant.scalar_one_or_none()
        
        gift_payload = [
            {
                "name": "Miccosmo Beppin Body Virgin White Serum 30g (Tặng thêm)",
                "qty": 1,
                "image": "/uploads/2026/04/535e0488-bca7-4035-935d-a8c3c022ab63.webp"
            }
        ]
        
        if variant:
            attrs = dict(variant.attributes or {})
            attrs["gifts"] = gift_payload
            variant.attributes = attrs
            print(f"Updated variant {variant.id} attributes: {json.dumps(variant.attributes, indent=2)}")
        else:
            print("Variant v_ea1b5d6f82ea not found.")
            
        # 2. Update Order 5464b1da-4196-4302-b7a1-69351ff7319b items to include gifts
        stmt_order = select(Order).where(Order.id == "5464b1da-4196-4302-b7a1-69351ff7319b")
        res_order = await session.execute(stmt_order)
        order = res_order.scalar_one_or_none()
        
        if order:
            items_list = list(order.items or [])
            updated = False
            for item in items_list:
                if item.get("id") == "prod_miccosmo_virgin_white" or item.get("variant_id") == "v_ea1b5d6f82ea":
                    item["gifts"] = gift_payload
                    updated = True
            
            if updated:
                order.items = items_list
                # Force SQLAlchemy to detect the JSON mutation
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(order, "items")
                
                # Also store it in order_metadata for redundancy
                meta = dict(order.order_metadata or {})
                meta["gifts_resolved"] = gift_payload
                order.order_metadata = meta
                flag_modified(order, "order_metadata")
                
                print(f"Updated order {order.id} items to include promotional gifts!")
            else:
                print("No matching item found in order items list to update.")
        else:
            print("Order 5464b1da-4196-4302-b7a1-69351ff7319b not found.")
            
        await session.commit()
        print("Database commit successful!")

if __name__ == "__main__":
    asyncio.run(fix_database())
