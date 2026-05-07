import os
import sys
import asyncio
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Fix python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

from backend.database import async_session_maker
from backend.database.models import ProductBase
from sqlalchemy import select

async def update_features():
    print(f"🚀 Updating FULL Viral features for ALL products in database...")
    
    async with async_session_maker() as session:
        # Find all products
        stmt = select(ProductBase)
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        if not products:
            print(f"❌ No products found in database.")
            return

        total = len(products)
        print(f"📦 Found {total} products. Starting bulk update...")

        for idx, product in enumerate(products):
            # Prepare metadata
            metadata = dict(product.product_metadata) if product.product_metadata else {}
            
            # --- 1. Flash Sale (Elite Pricing Intelligence) ---
            metadata["is_flash_sale"] = True
            if "flash_sale_end" not in metadata:
                future_date = datetime.now(timezone.utc) + timedelta(days=random.randint(3, 10))
                metadata["flash_sale_end"] = future_date.isoformat()
            
            # --- 2. Unified Viral Suite (Elite V2.2 Protocol) ---
            # Migrating from scattered root fields to a clean nested structure
            old_likes = metadata.get("likes") or random.randint(500, 8000)
            old_shares = metadata.get("share_count") or random.randint(100, 500)
            
            metadata["viral_suite"] = {
                "likes_count": old_likes,
                "share_count": old_shares,
                "share_target": 1000,
                "primary_campaign": "VOUCHER_UNLOCK", # Prioritize voucher campaign
                "share_promotion": {
                    "enabled": True,
                    "voucher_id": "VIRAL50K",
                    "voucher_label": "Giảm 50.000₫",
                    "cta_text": "Chia sẻ để nhận mã",
                    "share_text": f"Bí quyết tỏa sáng cùng {product.name}! Cùng chia sẻ để nhận ưu đãi 50K nhé! 🌸"
                }
            }
            
            # --- 3. Cleanup redundant fields to prevent UI duplication ---
            redundant_fields = [
                "likes", "share_count", "share_target", "share_promotion", 
                "share_reward_label", "offer_sales_label", "offer_rating_label"
            ]
            for field in redundant_fields:
                metadata.pop(field, None)
            
            product.product_metadata = metadata
            
            if (idx + 1) % 10 == 0:
                print(f"⏳ Processed {idx + 1}/{total} products...")
                # Optional: await session.flush() if total is huge, but for reasonable sets commit at end is fine
        
        await session.commit()
        print(f"✨ Successfully updated {total} products with FULL Viral 2026 suite.")
if __name__ == "__main__":
    asyncio.run(update_features())
