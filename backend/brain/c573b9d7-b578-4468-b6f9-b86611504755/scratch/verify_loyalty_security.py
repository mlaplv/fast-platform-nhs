import asyncio
import sys
import os

# Setup path to import backend
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from backend.database.models.commerce import UserLoyalty, PointTransaction
from backend.services.commerce.loyalty import LoyaltyService
from backend.database.models.auth import User

async def verify_security():
    # Use existing test/dev DB
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform")
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Check for a user
        stmt = select(User).limit(1)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        
        if not user:
            print("No user found to test.")
            return

        print(f"Testing security for user: {user.email}")
        
        # 2. Trigger auto-upgrade (Legacy to Seal)
        print("Step 2: Testing auto-upgrade of legacy data...")
        is_integrity_ok = await LoyaltyService.verify_loyalty_integrity(session, user.id)
        print(f"Initial Integrity check: {'OK' if is_integrity_ok else 'FAILED'}")
        
        # 3. Simulate tamper
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == user.id)
        res = await session.execute(stmt)
        loyalty = res.scalar_one_or_none()
        
        if loyalty:
            original_pts = loyalty.available_points
            print(f"Step 3: Simulating DB Tamper. Changing {original_pts} to {original_pts + 1000}...")
            loyalty.available_points += 1000
            await session.commit()
            
            # 4. Verify detection
            print("Step 4: Running Integrity Check after Tamper...")
            is_integrity_ok = await LoyaltyService.verify_loyalty_integrity(session, user.id)
            if not is_integrity_ok:
                print(">>> SUCCESS: Tampering detected!")
            else:
                print(">>> FAILED: Tampering NOT detected (Security failure).")
                
            # 5. Restore and reseal
            print("Step 5: Restoring balance and resealing...")
            loyalty.available_points = original_pts
            loyalty.balance_seal = LoyaltyService._create_balance_seal(loyalty)
            await session.commit()
            
            is_integrity_ok = await LoyaltyService.verify_loyalty_integrity(session, user.id)
            print(f"Final Integrity check after restoration: {'OK' if is_integrity_ok else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(verify_security())
