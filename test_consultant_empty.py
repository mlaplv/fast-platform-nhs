import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
from backend.services.commerce.operatives.handlers.base import SupportContext
from backend.database.alchemy_config import alchemy_config

async def main():
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as db:
        handler = ConsultantHandler()
        ctx = SupportContext(db=db, history_text="", cart_text="", product_ctx="")
        await handler.handle("[system_consult] Hãy tư vấn bán kem cổ hurri harry", ctx)
        print("REPLIES:", ctx.replies)
        print("INTENT:", ctx.intent)

asyncio.run(main())
