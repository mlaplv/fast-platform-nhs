import asyncio
from sqlalchemy import select
from backend.database.alchemy_config import alchemy_config
from backend.database.models.system import SupportKnowledge, SupportKnowledgeCategory

async def seed_beppin_knowledge():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        # Check if already exists
        q = select(SupportKnowledge).where(SupportKnowledge.question.like("%Beppin Body Virgin White Serum%"))
        res = await db.execute(q)
        if res.scalar():
            print("Knowledge for Beppin already exists. Skipping.")
            return

        k1 = SupportKnowledge(
            category=SupportKnowledgeCategory.PRODUCT,
            question="Miccosmo Beppin Body Virgin White Serum là gì và công nghệ nổi bật là gì?",
            answer=(
                "Dạ thưa Anh/Chị, Miccosmo Beppin Body Virgin White Serum là tinh chất dưỡng trắng chuyên sâu cho các vùng da nhạy cảm (nách, nhũ hoa, bikini). "
                "Điểm nổi bật nhất là **Công nghệ Nano-penetration (thẩm thấu vi hạt)** giúp các dưỡng chất thẩm thấu ngay lập tức vào lớp biểu bì mà không gây cảm giác bết dính. "
                "Cơ chế này giúp ức chế Melanin nhanh gấp 3 lần so với các loại kem bôi thông thường, mang lại hiệu quả rõ rệt sau 14 ngày sử dụng ạ! 🌸"
            ),
            tags={"product": "beppin", "tech": "nano"},
            priority=10
        )
        
        k2 = SupportKnowledge(
            category=SupportKnowledgeCategory.INFO_INGREDIENTS,
            question="Thành phần của serum Beppin có an toàn cho vùng nhạy cảm không?",
            answer=(
                "Dạ Anh/Chị yên tâm tuyệt đối ạ! Sản phẩm được thiết kế với triết lý 'An toàn là số 1' của Miccosmo Nhật Bản:\n"
                "1. **Chiết xuất nhau thai tan trong nước**: Ức chế tận gốc Melanin.\n"
                "2. **Dipotassium Glycyrrhizate**: Kháng viêm, làm dịu da vùng bikini.\n"
                "3. **Hyaluronic Acid kích thước Nano**: Cấp ẩm sâu, làm mềm mịn da.\n"
                "Đặc biệt: **CÔNG THỨC 3 KHÔNG**: Không Paraben, Không Cồn, Không Hương liệu nhân tạo, cực kỳ lành tính cho cả làn da nhạy cảm nhất ạ! ✨"
            ),
            tags={"product": "beppin", "safety": "high"},
            priority=10
        )

        db.add(k1)
        db.add(k2)
        await db.commit()
        print("Successfully seeded Beppin Deep Dive knowledge.")

if __name__ == "__main__":
    asyncio.run(seed_beppin_knowledge())
