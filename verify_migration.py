import asyncio
from sqlalchemy import text
from backend.database import async_session_maker

async def verify():
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'product_bases' AND column_name = 'order_count'"))
        row = result.fetchone()
        if row:
            print("VERIFICATION_SUCCESS: Column 'order_count' exists.")
        else:
            print("VERIFICATION_FAILURE: Column 'order_count' missing.")

if __name__ == "__main__":
    asyncio.run(verify())
