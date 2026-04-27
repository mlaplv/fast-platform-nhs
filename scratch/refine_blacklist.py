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
            
            # Remove the over-broad blocks
            if "3.1-flash" in blacklist: blacklist.remove("3.1-flash")
            if "3.1-pro" in blacklist: blacklist.remove("3.1-pro")
            
            # Add ONLY the problematic lite-preview
            if "lite-preview" not in blacklist:
                blacklist.append("lite-preview")
            
            val["blacklist"] = blacklist
            await s.execute(update(SystemSetting).where(SystemSetting.key == "ai_orchestration_config").values(value=val))
            await s.commit()
            print("✅ BLACKLIST REFINED (Allowed 3.1-pro/flash, kept lite-preview blocked)")
        else:
            print("❌ CONFIG NOT FOUND")

if __name__ == "__main__":
    asyncio.run(run())
