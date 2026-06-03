import os
from dotenv import load_dotenv
load_dotenv()

# Use container env or fallback
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform"
if "REDIS_URL" not in os.environ:
    os.environ["REDIS_URL"] = "redis://redis:6379/0"

import asyncio
import sys
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.services.commerce.operatives.support_agent import support_agent
from backend.schemas.support import SupportRequest
from backend.database.models.commerce import ProductBase
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    db_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(db_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as db:
        real_slug = "miccosmo-beppin-body-virgin-white-serum"
        print(f"Using real active slug: {real_slug}")
        
        # 1. Test "Công dụng"
        req_cong_dung = SupportRequest(
            message="Sản phẩm này có thành phần gì và công dụng như thế nào?",
            product_slug=real_slug,
            session_id="test-session-cong-dung"
        )
        print("\n=== TESTING CÔNG DỤNG ===")
        try:
            res = await support_agent.process_brain_logic(req_cong_dung, db)
            print(f"Reply: {res.reply}")
            print(f"Intent: {res.intent}")
            print(f"Status: {res.status}")
        except Exception as e:
            import traceback
            print(f"Failed: {e}")
            traceback.print_exc()
            
        # 2. Test "Tư vấn"
        req_tu_van = SupportRequest(
            message='[system_consult] Hãy tư vấn bán hàng chuyên sâu cho sản phẩm này theo cấu trúc chi tiết sau nhưng CẤM ghi tên các tiêu đề kỹ thuật:\n1. Đồng cảm sâu sắc với nỗi lo thầm kín nhất của khách hàng về làn da/vấn đề sản phẩm giải quyết.\n2. Liệt kê và phân tích chi tiết cơ chế khoa học của các thành phần nổi bật chuẩn Nhật dưới dạng danh sách (bullet points) rõ ràng.\n3. Vẽ ra bức tranh sinh động về sự tự tin rạng rỡ sau khi sử dụng.\n4. Đưa ra báo giá chi tiết (giá niêm yết, khuyến mãi), tồn kho thực tế (FOMO), chương trình KM và Kêu Gọi Hành Động (CTA) xin SĐT + Địa chỉ nhận hàng để chốt đơn ngay.\nCHÚ Ý: CẤM viết các tiêu đề thô kệch như "Điểm đau", "Giải pháp", "Viễn cảnh tự do", "Lời khuyên mua sắm từ Helen". Hãy chia đoạn tự nhiên bằng các emoji sang trọng.',
            product_slug=real_slug,
            session_id="test-session-tu-van"
        )
        print("\n=== TESTING TƯ VẤN ===")
        try:
            res2 = await support_agent.process_brain_logic(req_tu_van, db)
            print(f"Reply: {res2.reply}")
            print(f"Intent: {res2.intent}")
            print(f"Status: {res2.status}")
        except Exception as e:
            import traceback
            print(f"Failed: {e}")
            traceback.print_exc()

asyncio.run(main())
