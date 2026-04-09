import asyncio
from backend.database.models import Base
from backend.database import engine

async def init():
    async with engine.begin() as conn:
        # Run sync metadata creation
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init())
