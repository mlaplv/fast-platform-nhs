import asyncio
import os
import sys

# Load .env manually to ensure variables are available
def load_env():
    env_path = "/home/lv/Desktop/fast-platform-core/.env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    os.environ[k] = v

load_env()

# Modify DATABASE_URL if db host is not resolvable to localhost
db_url = os.environ.get("DATABASE_URL")
if db_url and "@db:" in db_url:
    # Check if host can resolve 'db'
    import socket
    try:
        socket.gethostbyname("db")
    except socket.gaierror:
        # Use localhost instead
        os.environ["DATABASE_URL"] = db_url.replace("@db:", "@localhost:")
        print(f"Redirecting DB connection to localhost: {os.environ['DATABASE_URL']}")

from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models import VoiceProfile, SystemSetting

async def check():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as s:
        # Check VoiceProfile
        p = (await s.execute(select(VoiceProfile).limit(1))).scalar_one_or_none()
        if p:
            print(f"VoiceProfile Primary Model: {p.primary_model}")
            print(f"VoiceProfile Waterfall: {p.ai_models}")
        else:
            print("No VoiceProfile found.")

        # Check SystemSetting
        setting = (await s.execute(
            select(SystemSetting).where(SystemSetting.key == "ai_orchestration_config")
        )).scalar_one_or_none()
        if setting:
            print(f"SystemSetting ai_orchestration_config: {setting.value}")
        else:
            print("No ai_orchestration_config SystemSetting found.")

if __name__ == "__main__":
    asyncio.run(check())
