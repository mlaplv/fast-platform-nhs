import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.services.commerce.operatives.support_agent import support_agent
from backend.schemas.support import SupportRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-sync-db")

async def test_all_sync_db_first():
    # Setup test connection using standard system config
    from backend.database.alchemy_config import alchemy_config
    async_session = alchemy_config.create_session_maker()

    test_cases = [
        {
            "name": "Quick Button 1: Tư vấn ([system_consult])",
            "message": "[system_consult] Hãy tư vấn cho tôi",
            "product_slug": "miccosmo-white-label-premium-placenta-wash-110g-sua-rua-mat-sach-sau-lam-diu-da"
        },
        {
            "name": "Quick Button 2: An toàn da ([system_skin_barrier])",
            "message": "[system_skin_barrier] Sản phẩm có an toàn không?",
            "product_slug": "miccosmo-white-label-premium-placenta-wash-110g-sua-rua-mat-sach-sau-lam-diu-da"
        },
        {
            "name": "Quick Button 3: Xuất xứ (xuất xứ)",
            "message": "Nguồn gốc xuất xứ sản phẩm ở đâu?",
            "product_slug": "miccosmo-white-label-premium-placenta-wash-110g-sua-rua-mat-sach-sau-lam-diu-da"
        },
        {
            "name": "Quick Button 4: Công dụng (công dụng)",
            "message": "Công dụng chính là gì?",
            "product_slug": "miccosmo-white-label-premium-placenta-wash-110g-sua-rua-mat-sach-sau-lam-diu-da"
        }
    ]

    async with async_session() as db:
        for tc in test_cases:
            logger.info(f"\n🚀 Running: {tc['name']}")
            req = SupportRequest(
                message=tc["message"],
                product_slug=tc["product_slug"],
                customer_name="Sếp",
                cart_items=[]
            )
            
            # Record start time
            import time
            start = time.perf_counter()
            
            # Execute chat in synchronous DB-First manner
            res = await support_agent.chat(req, db=db)
            duration = (time.perf_counter() - start) * 1000
            
            logger.info(f"⏱️ Duration: {duration:.2f}ms")
            logger.info(f"🟢 Status: {res.status}")
            logger.info(f"💬 Reply: {res.reply[:150]}...")
            
            # Assertions for 0ms gateway bypass
            assert res.status == "DONE", f"Expected 'DONE' status for fast-path bypass, got '{res.status}'"
            assert len(res.reply) > 50, "Reply should be detailed from DB-First context"

    logger.info("\n🟢 ALL SYNCHRONOUS DB-FIRST FAST-PATH TEST CASES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_all_sync_db_first())
