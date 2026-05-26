import asyncio
from sqlalchemy import delete
from backend.database import async_session_maker
from backend.database.models.promotion import Voucher

async def main():
    async with async_session_maker() as session:
        stmt = delete(Voucher).where(Voucher.id == "VIRAL79K")
        await session.execute(stmt)
        await session.commit()
        print("Successfully deleted VIRAL79K from DB.")

if __name__ == "__main__":
    asyncio.run(main())
