import asyncio
import os
import sys
from pathlib import Path

# Fix python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import async_session_maker
from backend.database.models import ProductBase
from sqlalchemy import select

async def check():
    async with async_session_maker() as session:
        result = await session.execute(select(ProductBase).where(ProductBase.name.like('%Beppin%')))
        p = result.scalar_one_or_none()
        if p:
            print(f"NAME: {p.name}")
            print("--- DESCRIPTION START ---")
            print(p.description)
            print("--- DESCRIPTION END ---")
        else:
            print("Product not found")

if __name__ == "__main__":
    asyncio.run(check())
