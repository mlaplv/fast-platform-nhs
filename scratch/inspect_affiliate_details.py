import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def run():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@db:5432/fast_platform')
    async with engine.connect() as conn:
        # 1. Get affiliate profile
        aff_res = await conn.execute(text("SELECT id FROM affiliate_profiles WHERE ctv_code = 'MLAP'"))
        aff = aff_res.fetchone()
        if not aff:
            print("Affiliate profile MLAP not found!")
            return
            
        # 2. Get commission ledgers for this affiliate from commission_ledger
        ledg_res = await conn.execute(text("SELECT id, order_id, affiliate_id, commission_amount, rate_applied, admin_note, status FROM commission_ledger WHERE affiliate_id = :aff_id"), {"aff_id": aff[0]})
        print("\n=== COMMISSION LEDGERS ===")
        for l in ledg_res.fetchall():
            print(f"Ledger ID: {l[0]} | Order ID: {l[1]} | Amount: {l[3]} | Rate: {l[4]} | Note: {l[5]} | Status: {l[6]}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
