import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.base import SupportContext, NeuralDNA
from backend.schemas.support import SupportRequest
from backend.schemas.order import OrderDraft

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as db:
        req = SupportRequest(message="tư vấn chuyên sâu về sản phẩm này", session_id="test_session")
        
        draft = OrderDraft(
            session_id="test_session",
            items=[{"id": "1", "name": "Test Product", "price": 100, "quantity": 1}],
            customer_phone=None,
            customer_address=None
        )
        
        ctx = SupportContext(
            db=db,
            request=req,
            session_id="test_session",
            dna=NeuralDNA(),
            order_draft=draft
        )
        
        handler = OrderHandler()
        result = await handler.handle(ctx)
        
        print(f"Result: {result}")
        print(f"Replies: {ctx.replies}")
        print(f"Lead Data: {ctx.lead_data}")

if __name__ == "__main__":
    asyncio.run(main())
