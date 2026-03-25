import asyncio
from backend.database.alchemy_config import alchemy_config
from backend.database.repositories import ContentCampaignRepository
from sqlalchemy import select
from backend.database.models import ContentCampaign

async def check():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        repo = ContentCampaignRepository(session=session)
        # Get last 5 campaigns
        stmt = select(ContentCampaign).order_by(ContentCampaign.created_at.desc()).limit(5)
        res = await session.execute(stmt)
        rows = res.scalars().all()
        for c in rows:
            topic = c.topic_data or {}
            has_report = 'scout_report' in topic
            print(f"ID: {c.id} | Topic: {topic.get('primary_keyword') or 'N/A'} | Has Report: {has_report}")
            if has_report:
                report = topic['scout_report']
                print(f"  - Report Topic: {report.get('topic')}")

if __name__ == "__main__":
    asyncio.run(check())
