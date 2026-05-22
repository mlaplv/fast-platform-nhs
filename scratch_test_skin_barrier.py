import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
from backend.services.commerce.operatives.handlers.base import SupportContext
from backend.schemas.support import SupportRequest
from backend.database.config import get_database_url
import logging
import sys
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def test():
    engine = create_async_engine(get_database_url())
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as db:
        request = SupportRequest(
            message='[system_skin_barrier] QUY TRÌNH KIỂM TRA HÀNG RÀO BẢO VỆ DA',
            product_slug='test-slug',
            session_id='test-session'
        )
        ctx = SupportContext(db=db, request=request, session_id='test-session')
        
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
