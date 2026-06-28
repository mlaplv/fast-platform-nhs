import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))
except ImportError:
    pass

from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import SystemSetting
from backend.schemas.system_settings import SeoContextualLinksSettings
from backend.services.xohi_memory import xohi_memory
from sqlalchemy import select

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        stmt = select(SystemSetting).where(SystemSetting.key == "primary_config")
        res = await session.execute(stmt)
        setting = res.scalar_one_or_none()
        
        if setting:
            val = dict(setting.value)
            
            default_settings = SeoContextualLinksSettings()
            if "seo_contextual_links" not in val:
                val["seo_contextual_links"] = {}
            
            val["seo_contextual_links"]["generic_exclusions"] = default_settings.generic_exclusions
            
            if "outbound_links" in val:
                del val["outbound_links"]
                
            setting.value = val
            session.add(setting)
            await session.commit()
            print("Successfully updated database primary_config settings.")
        else:
            print("No primary_config settings found in DB.")
            
        await xohi_memory.client.delete("system:settings:primary_config")
        await xohi_memory.client.delete("system:outbound_links_config")
        print("Successfully flushed Redis cache.")

if __name__ == "__main__":
    asyncio.run(main())
