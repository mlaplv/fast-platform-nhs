import asyncio
import os
import sys

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.database import db_session_maker
from backend.database.models import Order, ProductBase, ProductVariant
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def cleanup_dirty_snapshots():
    async with db_session_maker() as db_session:
        # Get orders that might have dirty variant_name
        stmt = select(Order)
        orders = (await db_session.execute(stmt)).scalars().all()
        
        updated_count = 0
        for order in orders:
            items = order.items
            if not getattr(order, "items", None):
                continue
            
            needs_update = False
            new_items = []
            for item in items:
                v_name = item.get("variant_name")
                v_id = item.get("variant_id")
                p_id = item.get("id")
                
                # Check if variant_name is dirty (contains brackets)
                if v_name and ("[" in v_name or "]" in v_name or "{" in v_name):
                    # Resolve real name
                    real_name = None
                    if v_id and p_id:
                        p_stmt = select(ProductBase).where(ProductBase.id == p_id)
                        p_res = await db_session.execute(p_stmt)
                        product = p_res.scalar_one_or_none()
                        
                        v_stmt = select(ProductVariant).where(ProductVariant.id == v_id)
                        v_res = await db_session.execute(v_stmt)
                        variant = v_res.scalar_one_or_none()
                        
                        if product and variant and getattr(variant, "tier_index", None) and getattr(product, "tier_variations", None):
                            tier_names = []
                            for i, t_idx in enumerate(variant.tier_index):
                                if i < len(product.tier_variations):
                                    tier = product.tier_variations[i]
                                    options = tier.get("options", [])
                                    if isinstance(options, list) and isinstance(t_idx, int) and t_idx < len(options):
                                        tier_names.append(str(options[t_idx]))
                            if tier_names:
                                real_name = " - ".join(tier_names)
                    
                    if real_name:
                        item["variant_name"] = real_name
                        needs_update = True
                    else:
                        item.pop("variant_name", None)
                        needs_update = True
                new_items.append(item)
            
            if needs_update:
                order.items = new_items
                updated_count += 1
                
        if updated_count > 0:
            await db_session.commit()
            print(f"✅ Successfully cleaned {updated_count} dirty order snapshots.")
        else:
            print("✨ No dirty snapshots found.")

if __name__ == "__main__":
    asyncio.run(cleanup_dirty_snapshots())
