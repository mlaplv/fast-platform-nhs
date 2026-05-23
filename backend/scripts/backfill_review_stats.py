import asyncio
from backend.database.session import AsyncSessionLocal
from backend.services.review_service import provide_review_service
from backend.database.repositories import SystemReviewRepository

async def main():
    async with AsyncSessionLocal() as session:
        repo = SystemReviewRepository(session=session)
        service = await provide_review_service(repo)
        
        # 1. Lấy danh sách các Product IDs có review đã APPROVED
        from sqlalchemy import select, func, and_
        from backend.database.models import SystemReview
        
        stmt = select(SystemReview.entity_id).where(and_(
            SystemReview.entity_type == "PRODUCT",
            SystemReview.status == "APPROVED"
        )).distinct()
        
        result = await session.execute(stmt)
        product_ids = [row[0] for row in result.fetchall()]
        
        print(f"Bắt đầu đồng bộ cho {len(product_ids)} sản phẩm có review đã duyệt...")
        
        # 2. Chạy _sync_product_rating cho từng ID
        for pid in product_ids:
            try:
                await service._sync_product_rating("PRODUCT", pid)
                print(f"  [OK] Đồng bộ {pid}")
            except Exception as e:
                print(f"  [LỖI] {pid}: {e}")
        
        print("HOÀN THÀNH!")

if __name__ == "__main__":
    asyncio.run(main())
