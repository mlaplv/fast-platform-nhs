import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.models import SystemSetting
from sqlalchemy import select, update
import json

async def run():
    async with alchemy_config.create_session_maker()() as s:
        res = await s.execute(select(SystemSetting).where(SystemSetting.key == "ai_orchestration_config"))
        row = res.scalar_one_or_none()
        if row:
            val = row.value
            blacklist = val.get("blacklist", [])
            to_add = ["lite-preview", "3.1-flash", "3.1-pro"] # Blocking all 3.1 for now if they are unstable
            updated = False
            for item in to_add:
                if item not in blacklist:
                    blacklist.append(item)
                    updated = True
            
            if updated:
                val["blacklist"] = blacklist
                await s.execute(update(SystemSetting).where(SystemSetting.key == "ai_orchestration_config").values(value=val))
                await s.commit()
                print("✅ BLACKLIST UPDATED IN DB")
            else:
                print("ℹ️ BLACKLIST ALREADY UP TO DATE")
        else:
            print("❌ CONFIG NOT FOUND")

if __name__ == "__main__":
    asyncio.run(run())
