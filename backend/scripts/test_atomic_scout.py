import asyncio
import httpx
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import ContentCampaignRepository
from sqlalchemy import select
from backend.database.models import ContentCampaign

async def test_atomic_scout():
    # 1. Get a campaign ID
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        repo = ContentCampaignRepository(session=session)
        stmt = select(ContentCampaign).order_by(ContentCampaign.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        c = res.scalar_one_or_none()
        if not c:
            print("No campaign found")
            return
        campaign_id = str(c.id)
        topic = c.topic_data.get("primary_keyword") or "thuốc hôi nách"
        print(f"Testing for Campaign: {campaign_id}, Topic: {topic}")

    # 2. Trigger Scout Logic directly (Atomic Sync)
    from backend.services.xohi.creative_studio.orchestrator import content_factory
    print(f"Triggering Atomic Scout for {topic}...")
    res = await content_factory.analyst.scout(topic, campaign_id=campaign_id)
    print(f"Handler Resp: {res.status}")

    # 3. Verify DB update
    async with session_maker() as session:
        repo = ContentCampaignRepository(session=session)
        # Refresh campaign from DB
        c = await repo.get(campaign_id)
        if c and c.topic_data and "scout_report" in c.topic_data:
            print("✅ SUCCESS: scout_report found in campaign topic_data!")
            print(f"   Report Topic: {c.topic_data['scout_report'].get('topic')}")
        else:
            print("❌ FAILURE: scout_report NOT found in campaign topic_data")
            if c: print(f"   Topic keys: {list(c.topic_data.keys())}")

if __name__ == "__main__":
    asyncio.run(test_atomic_scout())
