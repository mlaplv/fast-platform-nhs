import os
import sys
from pathlib import Path

# Thêm project root vào sys.path để import được các module của backend
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path: 
    sys.path.insert(0, project_root)

import asyncio
import uuid
import random
from sqlalchemy import select
from dotenv import load_dotenv

# Load môi trường
load_dotenv(os.path.realpath(os.path.join(os.path.dirname(__file__), "../../.env")))

from backend.database import async_session_maker
from backend.database.models.system import SystemReview, ReviewEntityType
from backend.database.models.content import Category

TENANT_ID = "smartshop" # Sử dụng tenant ID chuẩn của Micsmo

NAMES = [
    "Nguyễn Thu Thủy", "Trần Minh Tâm", "Lê Hải Yến", "Phạm Hoàng Nam", 
    "Đặng Thùy Chi", "Hoàng Gia Bảo", "Vũ Phương Thảo", "Bùi Anh Đức",
    "Lý Kim Ngân", "Đỗ Mạnh Hùng", "Ngô Thanh Vân", "Trịnh Công Sơn"
]

LOCATIONS = ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Cần Thơ", "Hải Phòng", "Bình Dương", "Nha Trang", "Vũng Tàu"]

# Nội dung review được tinh chỉnh để đạt hiệu quả Viral cao (Vietnamese Elite Style)
REVIEW_TEMPLATES = [
    "Sự lựa chọn hoàn hảo! Danh mục này tập hợp toàn những siêu phẩm chất lượng nhất mình từng dùng. Highly recommend cho mọi người! ✨",
    "Micsmo luôn mang đến trải nghiệm đẳng cấp. Các sản phẩm trong nhóm này rất đa dạng, tư vấn chuyên nghiệp và tận tâm cực kỳ. 5 sao không cần bàn cãi! 🌟",
    "Giao hàng siêu tốc, đóng gói cực kỳ sang chảnh. Danh mục này hội tụ đủ các tiêu chí: Xịn - Sang - Mịn. Sẽ còn ủng hộ shop nhiều lần nữa! 💎",
    "Rất hài lòng với dịch vụ và chất lượng ở đây. Các sản phẩm trong mục này đều chuẩn auth, dùng là thấy sự khác biệt ngay. Đáng đồng tiền bát gạo! ✅",
    "Đỉnh của chóp luôn ạ! Danh mục này toàn hàng hot hit mà giá lại cực kỳ ưu đãi. Viral mạnh cho team Micsmo vì sự tử tế và chuyên nghiệp! 🚀",
    "Trải nghiệm mua sắm tuyệt vời nhất từ trước đến nay. Danh mục này thực sự rất được đầu tư về chất lượng sản phẩm. Rất hài lòng! ❤️",
    "Cảm ơn Micsmo vì đã mang về những sản phẩm chất lượng như thế này. Danh mục này giúp mình tiết kiệm rất nhiều thời gian lựa chọn. Tuyệt vời! 🌈"
]

async def seed_category_reviews():
    print("🚀 Đang bắt đầu quá trình Seeding Đánh giá Danh mục (Viral 2026)...")
    
    async with async_session_maker() as session:
        try:
            # Lấy tất cả danh mục đang hoạt động (không bị xóa mềm)
            result = await session.execute(select(Category).where(Category.deleted_at == None))
            categories = result.scalars().all()
            
            if not categories:
                print("⚠️ Không tìm thấy danh mục nào để seeding.")
                return

            print(f"📦 Tìm thấy {len(categories)} danh mục. Đang tạo 3 đánh giá viral cho mỗi danh mục...")
            
            count = 0
            for cat in categories:
                # Chọn 3 mẫu review ngẫu nhiên không trùng lặp
                templates = random.sample(REVIEW_TEMPLATES, 3)
                for i in range(3):
                    review = SystemReview(
                        id=str(uuid.uuid4()),
                        entity_type=ReviewEntityType.CATEGORY,
                        entity_id=cat.id,
                        customer_name=random.choice(NAMES),
                        customer_location=random.choice(LOCATIONS),
                        rating=5,
                        content=templates[i],
                        status="APPROVED",
                        tenant_id=cat.tenant_id or TENANT_ID,
                        likes_count=random.randint(50, 500)
                    )
                    session.add(review)
                    count += 1
            
            await session.commit()
            print(f"✨ Thành công: Đã thêm {count} đánh giá chuyên nghiệp cho {len(categories)} danh mục!")
            print("🚀 Dữ liệu đã được cập nhật an toàn mà không ảnh hưởng đến đánh giá cũ.")
            
        except Exception as e:
            print(f"❌ Lỗi trong quá trình seeding: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(seed_category_reviews())
