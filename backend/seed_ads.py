import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import insert
from backend.database.alchemy_config import alchemy_config
from backend.database.models.ads import ClickFraudEvent, IPBlacklist, NegativeKeyword

async def seed():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        print("🌱 Seeding Ads Protection data...")
        
        # 1. Click Fraud Events (10 mẫu)
        events = [
            {
                "ip_address": f"103.56.{i}.{i*2}",
                "fraud_score": 0.85 if i % 3 == 0 else 0.15,
                "verdict": "FRAUD" if i % 3 == 0 else "CLEAN",
                "ip_country": "VN",
                "ip_org": "Viettel Network",
                "is_datacenter": False,
                "session_duration_ms": 1200 if i % 3 == 0 else 45000,
                "triggered_signals": '["instant_bounce", "zero_scroll"]' if i % 3 == 0 else '[]',
                "campaign_id": "8120678827",
                "gclid": f"gclid_mock_{i}",
                "created_at": datetime.now(timezone.utc) - timedelta(hours=i)
            } for i in range(10)
        ]
        for e in events:
            await db.execute(insert(ClickFraudEvent).values(**e))
            
        # 2. Blacklist (2 mẫu)
        await db.execute(insert(IPBlacklist).values(
            ip_address="45.124.84.112",
            reason="Tấn công botnet liên tục (Xohi detected)",
            fraud_score=0.98,
            country="RU",
            org="Digital Ocean LLC"
        ))
        
        # 3. Negative Keywords (3 mẫu)
        await db.execute(insert(NegativeKeyword).values(
            keyword_text="miễn phí",
            match_type="PHRASE",
            campaign_id="8120678827"
        ))
        await db.execute(insert(NegativeKeyword).values(
            keyword_text="lừa đảo",
            match_type="EXACT"
        ))
        
        await db.commit()
        print("✅ Seed completed!")

if __name__ == "__main__":
    asyncio.run(seed())
