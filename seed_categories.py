import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.alchemy_config import alchemy_config
from backend.services.commerce.category import category_service
from backend.schemas.category import CreateCategoryRequest

async def seed_categories():
    # Setup session
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db_session:
        categories = [
            {"name": "Serum", "slug": "serum"},
            {"name": "Kem dưỡng", "slug": "kem-duong"},
            {"name": "Mặt nạ", "slug": "mat-na"},
            {"name": "Chăm sóc mắt", "slug": "cham-soc-mat"},
        ]

        for cat in categories:
            # Create a new session for each category to ensure a fresh transaction
            async with session_maker() as db_session:
                data = CreateCategoryRequest(
                    name=cat["name"],
                    slug=cat["slug"]
                )
                try:
                    await category_service.create_category(db_session, data)
                    print(f"Seeded category: {cat['name']}")
                except Exception as e:
                    print(f"Failed to seed {cat['name']}: {e}")
        print("Seed data completed.")

if __name__ == "__main__":
    asyncio.run(seed_categories())
