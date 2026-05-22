import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
from backend.services.commerce.operatives.handlers.base import SupportContext
from backend.schemas.support import SupportRequest
from backend.database.config import get_database_url
from backend.database.models.commerce import ProductBase, Order
from backend.services.xohi_memory import xohi_memory
import logging
import sys
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def test():
    engine = create_async_engine(get_database_url())
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as db:
        request = SupportRequest(
            message='[system_skin_barrier] QUY TRÌNH KIỂM TRA HÀNG RÀO BẢO VỆ DA (SKIN BARRIER):\n1. ĐÓNG VAI LÀ HELEN - CHUYÊN GIA DA LIỄU AI ÂN CẦN.\n2. KHOAN TƯ VẤN SẢN PHẨM NGAY. Hãy chào khách và CHỦ ĐỘNG hỏi thăm tình trạng da hiện tại của họ (ví dụ: da có đang mẩn đỏ, nhạy cảm, hay đang dùng treatment nặng như BHA/Retinol không?).\n3. GIẢI THÍCH NGẮN GỌN rằng Helen cần thông tin này để đối chiếu với Bảng Thành Phần (Ingredients) của sản phẩm, nhằm đánh giá xem sản phẩm có an toàn tuyệt đối cho "hàng rào bảo vệ da" của riêng khách hay không.\n4. CẤM BÁO GIÁ HAY CHỐT SALE Ở BƯỚC NÀY. Chỉ tập trung hỏi thăm và chờ khách hàng trả lời.',
            product_slug='test-slug',
            session_id='test-session'
        )
        ctx = SupportContext(db=db, request=request, session_id='test-session')
        # Setup mock active draft to test sticky bypass
        from backend.schemas.order import OrderDraft
        ctx.order_draft = OrderDraft(session_id="test-session", items=[])
        
        print('--- Testing OrderHandler ---')
        order_handler = OrderHandler()
        order_res = await order_handler.handle(ctx)
        print(f'OrderHandler returned: {order_res}')
        if ctx.replies: print(f'Replies from Order: {ctx.replies}')
        
        if not order_res:
            print('--- Testing ConsultantHandler ---')
            consultant = ConsultantHandler()
            consultant_res = await consultant.handle(ctx)
            print(f'ConsultantHandler returned: {consultant_res}')
            if ctx.replies: print(f'Replies from Consultant: {ctx.replies}')

asyncio.run(test())
