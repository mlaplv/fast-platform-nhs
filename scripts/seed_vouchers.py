import asyncio
import logging
from sqlalchemy.future import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.promotion import Voucher
from backend.constants.tenants import APP_DOMAIN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed-vouchers")

VOUCHERS_DATA = [
    {
        "id": "FREESHIP30",
        "type": "SHIPPING",
        "title": "Miễn Phí Vận Chuyển",
        "subtitle": "GIẢM TỐI ĐA 30,000Đ",
        "value": 30000,
        "min_spend": 0,
        "is_active": True,
        "tenant_id": APP_DOMAIN
    },
    {
        "id": "FREESHIP60",
        "type": "SHIPPING",
        "title": "Miễn Phí Vận Chuyển",
        "subtitle": "GIẢM TỐI ĐA 60,000Đ",
        "value": 60000,
        "min_spend": 0,
        "is_active": True,
        "tenant_id": APP_DOMAIN
    },
    {
        "id": "DISC30K",
        "type": "FIXED",
        "title": "Giảm ₫30k",
        "subtitle": "ĐƠN TỪ 150K",
        "value": 30000,
        "min_spend": 150000,
        "is_active": True,
        "tenant_id": APP_DOMAIN
    },
    {
        "id": "DISC60K",
        "type": "FIXED",
        "title": "Giảm ₫60k",
        "subtitle": "ĐƠN TỪ 300K",
        "value": 60000,
        "min_spend": 300000,
        "is_active": True,
        "tenant_id": APP_DOMAIN
    }
]

async def seed_vouchers():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        for data in VOUCHERS_DATA:
            # Check if voucher already exists
            stmt = select(Voucher).where(Voucher.id == data["id"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"Voucher {data['id']} already exists. Updating...")
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                logger.info(f"Creating voucher {data['id']}...")
                voucher = Voucher(**data)
                session.add(voucher)
        
        await session.commit()
        logger.info("Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_vouchers())
