import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import alchemy_config
from sqlalchemy import text
from backend.database.models.seo import SeoContextualLink

async def run():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        res = await db.execute(text("SELECT id, status FROM seo_contextual_links LIMIT 1"))
        row = res.first()
        if row:
            print(f"Raw DB row status: {row.status} (type: {type(row.status)})")
            
        # Try loading via SQLAlchemy model
        from sqlalchemy import select
        link = await db.scalar(select(SeoContextualLink).limit(1))
        if link:
            print(f"SQLAlchemy model status: {link.status}")
            print(f"Type: {type(link.status)}")
            print(f"Isinstance of str: {isinstance(link.status, str)}")
            print(f"Value: {getattr(link.status, 'value', None)}")
            print(f"Name: {getattr(link.status, 'name', None)}")

if __name__ == "__main__":
    asyncio.run(run())
