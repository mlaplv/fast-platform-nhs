import asyncio
from backend.database.session import SessionLocal
from backend.database.models import Category
from sqlalchemy import select

async def run():
    async with SessionLocal() as db:
        res = await db.execute(select(Category))
        cats = res.scalars().all()
        for c in cats:
            print(f"Name: {c.name}, Slug: {c.slug}, Image: {c.image}")

if __name__ == "__main__":
    asyncio.run(run())
