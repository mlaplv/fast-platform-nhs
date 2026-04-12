import os
import sys
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path: sys.path.insert(0, project_root)

import asyncio
import uuid
from sqlalchemy import select, delete
from dotenv import load_dotenv

load_dotenv(os.path.realpath(os.path.join(os.path.dirname(__file__), "../../.env")))

from backend.database import async_session_maker
from backend.database.models.system import SystemReview
from backend.scripts.seed_data import PRODUCT_DEFS

TENANT_ID = "smartshop"

async def seed_reviews():
    print("🌟 Starting Polymorphic Review Seeding...")
    async with async_session_maker() as session:
        try:
            # 1. Clear old reviews
            print("🧹 Clearing old SystemReviews...")
            await session.execute(delete(SystemReview).where(SystemReview.tenant_id == TENANT_ID))
            await session.flush()

            # 2. Extract reviews from Product Defs
            reviews_data = PRODUCT_DEFS[0].get("product_metadata", {}).get("reviews", [])
            print(f"📦 Found {len(reviews_data)} reviews in seed data. Seeding...")

            for r in reviews_data:
                review_db = SystemReview(
                    id=str(uuid.uuid4()),
                    entity_type="PRODUCT",
                    entity_id="prod_miccosmo_virgin_white",
                    customer_name=r.get("name", "Khách hàng"),
                    customer_phone=r.get("phone", ""),
                    customer_location=r.get("location", "Việt Nam"),
                    rating=r.get("rating", 5),
                    content=r.get("content", ""),
                    status="APPROVED",
                    tenant_id=TENANT_ID,
                    attributes=r.get("attributes"),
                    attachments=r.get("attachments"),
                    likes_count=r.get("likes_count", 0)
                )
                session.add(review_db)
            
            await session.commit()
            print("✨ Successfully seeded reviews into realdb!")
            
        except Exception as e:
            print(f"❌ Error during review seeding: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_reviews())
