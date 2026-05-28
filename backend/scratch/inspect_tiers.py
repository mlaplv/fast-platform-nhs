import asyncio
from sqlalchemy import select
from backend.database import alchemy_config
from backend.database.models import AffiliateProfile, CommissionTier

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        # Load all tiers
        tiers_res = await session.execute(select(CommissionTier))
        tiers = tiers_res.scalars().all()
        print("COMMISSION TIERS IN DATABASE:")
        for t in tiers:
            print(f"- ID: {t.id}, Name: {t.name}, Rate: {t.commission_rate}, Min Revenue: {t.min_revenue_threshold}, Default: {t.is_default}")
        
        # Load affiliate MLAP
        aff_res = await session.execute(select(AffiliateProfile).where(AffiliateProfile.ctv_code == 'MLAP'))
        aff = aff_res.scalar_one_or_none()
        if aff:
            print(f"\nMLAP PROFILE:")
            print(f"- ID: {aff.id}, Code: {aff.ctv_code}, Tier ID: {aff.tier_id}, Status: {aff.status}")
        else:
            print("\nAffiliate MLAP not found")

if __name__ == "__main__":
    asyncio.run(main())
