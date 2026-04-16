import asyncio
import logging
from sqlalchemy import update
from backend.database.alchemy_config import alchemy_config
from backend.database.models.promotion import Voucher
from backend.constants.tenants import APP_DOMAIN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix-vouchers")

async def fix_vouchers():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        logger.info(f"Migrating vouchers to tenant: {APP_DOMAIN}")
        stmt = (
            update(Voucher)
            .where(Voucher.tenant_id == "default")
            .values(tenant_id=APP_DOMAIN)
        )
        result = await session.execute(stmt)
        await session.commit()
        logger.info(f"Successfully updated {result.rowcount} vouchers.")

if __name__ == "__main__":
    asyncio.run(fix_vouchers())
