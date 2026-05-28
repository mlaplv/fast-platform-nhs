import asyncio
from sqlalchemy import select, and_, func
from backend.database.alchemy_config import alchemy_config
from backend.database.models.affiliate import AffiliateProfile, CommissionLedger, WithdrawalRequest
from backend.database.models.auth import User

async def inspect():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # Get all profiles
        stmt = select(AffiliateProfile)
        res = await db.execute(stmt)
        profiles = res.scalars().all()
        print(f"Total affiliate profiles: {len(profiles)}")
        for p in profiles:
            print(f"ID: {p.id} | UserID: {p.user_id} | Code: {p.ctv_code} | Status: {p.status} | DeletedAt: {p.deleted_at}")
            
            # Check pending commission
            pending_stmt = select(func.sum(CommissionLedger.commission_amount)).where(
                and_(
                    CommissionLedger.affiliate_id == p.id,
                    CommissionLedger.status == "PENDING"
                )
            )
            pending_res = await db.execute(pending_stmt)
            pending_amount = float(pending_res.scalar() or 0.0)
            
            # Check pending withdrawals
            pending_wr_stmt = select(func.count()).select_from(WithdrawalRequest).where(
                and_(
                    WithdrawalRequest.affiliate_id == p.id,
                    WithdrawalRequest.status.in_(["PENDING", "APPROVED"])
                )
            )
            pending_wr_res = await db.execute(pending_wr_stmt)
            pending_wr_count = pending_wr_res.scalar() or 0
            
            print(f"  -> Pending Commission: {pending_amount:,.0f}đ")
            print(f"  -> Pending Withdrawal Requests: {pending_wr_count}")

if __name__ == "__main__":
    asyncio.run(inspect())
