import os
import sys
import json
from pathlib import Path

# Setup project paths
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models import ProductBase

async def main():
    print("=== [FAQ Restore] Starting FAQ restoration from backup ===")
    
    json_path = Path("/app/backups/safety_net/virgin_white_faqs.json")
    if not json_path.exists():
        print(f"❌ Error: Backup JSON file not found at {json_path}")
        return
        
    with open(json_path, "r", encoding="utf-8") as f:
        faqs = json.load(f)
        
    print(f"✔ Read {len(faqs)} FAQs from backup JSON.")
    
    async with async_session_maker() as session:
        try:
            # Fetch product base
            stmt = select(ProductBase).where(ProductBase.id == "prod_miccosmo_virgin_white")
            product = (await session.execute(stmt)).scalar_one_or_none()
            
            if not product:
                print("❌ Error: Product 'prod_miccosmo_virgin_white' not found in database!")
                return
                
            print(f"✔ Found product in DB: {product.name} (ID: {product.id})")
            
            # Prepare new metadata
            metadata = dict(product.product_metadata or {})
            old_faqs = metadata.get("faqs", [])
            print(f"  Current FAQs in DB: {len(old_faqs)}")
            
            # Update FAQs and total count
            metadata["faqs"] = faqs
            metadata["faqs_total"] = len(faqs)
            
            # Save back to database
            product.product_metadata = metadata
            session.add(product)
            await session.commit()
            
            print(f"🎉 Successfully restored {len(faqs)} FAQs for product '{product.id}' in active DB!")
            
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(main())
