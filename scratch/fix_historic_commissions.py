import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import json

from backend.database.models.affiliate import AffiliateProfile, CommissionLedger, CommissionTier
from backend.services.ctv_service import _create_balance_seal

async def run():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@db:5432/fast_platform')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        async with session.begin():
            # 1. Fetch Bronze tier for osmo.vn
            tier_res = await session.execute(
                select(CommissionTier)
                .where(CommissionTier.tenant_id == 'osmo.vn')
                .where(CommissionTier.name == 'Đồng')
            )
            bronze_tier = tier_res.scalar_one_or_none()
            if not bronze_tier:
                print("Bronze tier for osmo.vn not found!")
                return
            print(f"Found Bronze Tier: {bronze_tier.id} ({bronze_tier.commission_rate * 100}%)")
            
            # 2. Fetch affiliate profile for MLAP
            aff_res = await session.execute(
                select(AffiliateProfile)
                .where(AffiliateProfile.ctv_code == 'MLAP')
            )
            aff = aff_res.scalar_one_or_none()
            if not aff:
                print("Affiliate MLAP not found!")
                return
            print(f"Found Affiliate Profile: {aff.id}, current tier: {aff.commission_tier_id}")
            
            # Update tier
            aff.commission_tier_id = bronze_tier.id
            
            # 3. Fetch ledgers
            ledg_res = await session.execute(
                select(CommissionLedger)
                .where(CommissionLedger.affiliate_id == aff.id)
            )
            ledgers = ledg_res.scalars().all()
            
            total_comm = 0.0
            for l in ledgers:
                if l.rate_applied == 0.15:
                    print(f"Updating ledger {l.id} from 15% to 5%...")
                    l.rate_applied = 0.05
                    # New correct calculation: (606,735 - 25,000) * 0.97 * 0.05 = 28,214.15
                    l.commission_amount = 28214.15
                    
                    breakdown = {
                        "order_total": 606735.0,
                        "shipping_fee": 25000.0,
                        "tax_rate": 0.03,
                        "tax_deduction": 17452.05,
                        "revenue_net": 564282.95,
                        "rate_applied": 0.05,
                        "commission_amount": 28214.15
                    }
                    l.admin_note = json.dumps(breakdown)
                    
                    # Update integrity token
                    from backend.services.ctv_service import GeminiSecurity
                    l.integrity_token = GeminiSecurity.encrypt({
                        "id": l.id,
                        "o": l.order_id,
                        "a": str(round(l.commission_amount, 2)),
                    })
                total_comm += l.commission_amount
            
            # Update affiliate totals
            aff.total_commission = total_comm
            aff.balance_seal = _create_balance_seal(aff)
            
            print(f"Updated affiliate MLAP total commission: {aff.total_commission}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
