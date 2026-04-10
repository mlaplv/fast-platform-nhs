import asyncio
import os
import sys
import json
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path: sys.path.insert(0, project_root)

from sqlalchemy import select
from backend.database import async_session_maker
from backend.database.models import SystemSetting

async def get_settings():
    async with async_session_maker() as session:
        stmt = select(SystemSetting).where(SystemSetting.key == "primary_config")
        result = await session.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            print(json.dumps(setting.value, indent=4, ensure_ascii=False))
        else:
            print("No setting found for 'primary_config'")

if __name__ == "__main__":
    asyncio.run(get_settings())
