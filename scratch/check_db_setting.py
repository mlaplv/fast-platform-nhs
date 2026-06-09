import asyncio
import os
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv("/app/.env")

# Override DATABASE_URL to use localhost/db depending on execution context
# The docker container will use db:5432, which is already configured.

from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import SystemSetting
from sqlalchemy import select

async def main():
    async_session = alchemy_config.create_session_maker()
    async with async_session() as session:
        stmt = select(SystemSetting).where(SystemSetting.key.in_(["LOYALTY_POINT_VALUE_VND", "LOYALTY_CHECKIN_CONFIG"]))
        res = await session.execute(stmt)
        settings = res.scalars().all()
        if not settings:
            print("No loyalty settings found in database system_settings table.")
        for setting in settings:
            print(f"Setting key: {setting.key}, value: {setting.value}")

if __name__ == "__main__":
    asyncio.run(main())
