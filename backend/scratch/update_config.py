import asyncio
import os
import sys
import json

# Load .env file
def load_env():
    env_path = "/media/lv/data/fast-platform-core/.env"
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        os.environ[key] = val

load_env()
sys.path.append("/media/lv/data/fast-platform-core")

from sqlalchemy import select, update
from backend.database.alchemy_config import alchemy_config
from backend.database.models import SystemSetting

async def main():
    async with alchemy_config.create_session_maker()() as session:
        setting = (await session.execute(
            select(SystemSetting).where(SystemSetting.key == "ai_orchestration_config")
        )).scalar_one_or_none()
        
        if not setting:
            print("No setting found in DB!")
            return
            
        config = dict(setting.value)
        mapping = config.setdefault("error_mapping", {})
        
        # Adjust auth_hard
        hard = mapping.setdefault("auth_hard", [])
        for item in ["denied access", "permission_denied"]:
            if item not in hard:
                hard.append(item)
                
        # Remove from auth_soft
        soft = mapping.setdefault("auth_soft", [])
        mapping["auth_soft"] = [x for x in soft if x not in ["permission_denied"]]
        
        setting.value = config
        session.add(setting)
        await session.commit()
        print("Successfully updated DB ai_orchestration_config!")
        print(json.dumps(config, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
