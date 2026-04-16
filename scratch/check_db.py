import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models.promotion import Voucher
from sqlalchemy.future import select

async def check_vouchers():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        stmt = select(Voucher)
        result = await session.execute(stmt)
        vouchers = result.scalars().all()
        print(f"Total Vouchers: {len(vouchers)}")
        for v in vouchers:
            print(f"- ID: {v.id}, Tenant: {v.tenant_id}, Active: {v.is_active}")

if __name__ == "__main__":
    asyncio.run(check_vouchers())
