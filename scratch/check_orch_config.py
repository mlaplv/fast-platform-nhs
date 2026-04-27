import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models import SystemSetting
from sqlalchemy import select
import json

async def run():
    async with alchemy_config.create_session_maker()() as s:
        res = await s.execute(select(SystemSetting).where(SystemSetting.key == "ai_orchestration_config"))
        row = res.scalar_one_or_none()
        if row:
            print(json.dumps(row.value, indent=2))
        else:
            print("NOT FOUND")

if __name__ == "__main__":
    asyncio.run(run())
