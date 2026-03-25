import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import ContentCampaignRepository
from sqlalchemy import select
from backend.database.models import ContentCampaign

async def audit_scouting_active():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        stmt = select(ContentCampaign).order_by(ContentCampaign.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        c = res.scalar_one_or_none()
        if c:
            gold = c.gold_metadata or {}
            config = gold.get("creation_config", {})
            active = config.get("scouting_active")
            print(f"Campaign ID: {c.id}")
            print(f"Scouting Active Flag: {active}")
            if active:
                print("✅ SUCCESS: scouting_active is True in DB!")
            else:
                print("❌ FAILURE: scouting_active is NOT True in DB")
        else:
            print("No campaign found")

if __name__ == "__main__":
    asyncio.run(audit_scouting_active())
