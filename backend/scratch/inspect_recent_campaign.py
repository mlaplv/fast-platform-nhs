import asyncio
import logging
import sys
import os
from sqlalchemy import select

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

from backend.database.alchemy_config import alchemy_config
from backend.database.models.content import ContentCampaign

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        # Get the latest campaigns
        stmt = select(ContentCampaign).order_by(ContentCampaign.updated_at.desc()).limit(5)
        res = await session.execute(stmt)
        campaigns = res.scalars().all()
        
        for c in campaigns:
            print(f"--- Campaign ID: {c.id} ---")
            print(f"Title: {c.title}")
            print(f"Slug: {c.slug}")
            print(f"Updated At: {c.updated_at}")
            print(f"Draft Content Length: {len(c.draft_content or '')}")
            print(f"Gold Metadata: {c.gold_metadata}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
