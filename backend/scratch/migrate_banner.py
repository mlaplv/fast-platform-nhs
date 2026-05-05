import asyncio
from sqlalchemy import text
from backend.database import async_session_maker

async def migrate():
    try:
        async with async_session_maker() as session:
            await session.execute(text("ALTER TABLE banners ADD COLUMN mobile_image_url VARCHAR;"))
            await session.commit()
            print("Successfully added mobile_image_url to banners")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
