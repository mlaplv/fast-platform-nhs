import asyncio
import logging
import sys
from sqlalchemy import select
from backend.database.models import Base
from backend.database import async_session_maker
from backend.database.models.affiliate import AffiliateProfile
from backend.database.models.commerce import UserLoyalty
from backend.services.ctv_service import _create_balance_seal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seal-regenerator")

async def regenerate_seals():
    logger.info("🚀 Bắt đầu chiến dịch tái cấu trúc và tái tạo chữ ký bảo mật (Seal Regeneration)...")
    
    async with async_session_maker() as session:
        # 1. Tái tạo Seal cho Affiliate Profiles
        logger.info("⏳ Đang xử lý Affiliate Profiles...")
        stmt_aff = select(AffiliateProfile)
        result_aff = await session.execute(stmt_aff)
        affiliates = result_aff.scalars().all()
        
        aff_count = 0
        for aff in affiliates:
            # Force conversion sang int để đảm bảo kiểu dữ liệu đồng nhất
            aff.total_revenue = int(aff.total_revenue or 0)
            aff.total_commission = int(aff.total_commission or 0)
            aff.paid_commission = int(aff.paid_commission or 0)
            
            # Tạo seal mới bằng thuật toán AES-GCM bảo mật quân sự
            new_seal = _create_balance_seal(aff)
            aff.balance_seal = new_seal
            aff_count += 1
            
        # 2. Tái tạo Seal cho User Loyalty
        logger.info("⏳ Đang xử lý User Loyalty...")
        stmt_loyalty = select(UserLoyalty)
        result_loyalty = await session.execute(stmt_loyalty)
        loyalties = result_loyalty.scalars().all()
        
        loy_count = 0
        for loy in loyalties:
            loy.total_spent = int(loy.total_spent or 0)
            # Tạo seal mới cho loyalty (chữ ký bảo mật điểm tiêu dùng tích lũy)
            from backend.utils.security import GeminiSecurity
            loy.balance_seal = GeminiSecurity.encrypt({
                "id": loy.id,
                "spent": str(loy.total_spent),
                "available_points": str(loy.available_points),
                "pending_points": str(loy.pending_points)
            })
            loy_count += 1
            
        # Commit giao dịch nguyên tử
        if aff_count > 0 or loy_count > 0:
            await session.commit()
            logger.info(f"✅ Thành công! Đã tái tạo cấu trúc seal bảo mật cho {aff_count} Affiliates và {loy_count} Loyalty profiles.")
        else:
            logger.info("ℹ️ Không tìm thấy bản ghi nào cần tái tạo.")

if __name__ == "__main__":
    try:
        asyncio.run(regenerate_seals())
    except Exception as e:
        logger.exception(f"❌ Thất bại trong quá trình tái tạo seal: {e}")
        sys.exit(1)
