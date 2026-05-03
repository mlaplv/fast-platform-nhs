import asyncio
import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete

# Import models & service
# Note: In the test environment, we need to mock or use the real DB
# Since we are on the user's machine, let's try to connect to the actual DB container
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/fast_platform"

import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.database.models.system import ChatMessage
from backend.services.chat_service import ChatService

async def test_keyset_pagination():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    user_id = "fc9941be-8e50-4020-a252-9e3e30134aee" # Real user ID from DB
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    
    async with async_session() as session:
        # 1. Clean up old test data
        await session.execute(delete(ChatMessage).where(ChatMessage.user_id == user_id))
        
        # 2. Insert 60 messages (Max limit is 50, so we need 2 pages)
        print(f"Inserting 60 messages for user {user_id}...")
        now = datetime.now(timezone.utc)
        messages = []
        for i in range(60):
            msg = ChatMessage(
                id=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                role="user",
                content={"text": f"Message {i:03d}"},
                created_at=now - timedelta(seconds=i), # i=0 is newest
                tenant_id="default"
            )
            session.add(msg)
            messages.append(msg)
        
        await session.commit()
        
        # 3. Test Page 1 (Newest 50)
        print("Fetching Page 1...")
        history_p1_resp = await ChatService.get_history(
            db_session=session,
            session_id=session_id,
            user_id=user_id,
            roles=["USER"],
            limit=50
        )
        
        history_p1 = history_p1_resp.messages
        cursor_p1 = history_p1_resp.next_cursor
        
        print(f"Page 1 results: {len(history_p1)}")
        assert history_p1[0].content['text'] == "Message 049"
        assert history_p1[-1].content['text'] == "Message 000"
        assert cursor_p1 is not None
        
        # 4. Test Page 2 (Remaining 10)
        print(f"Fetching Page 2 with cursor: {cursor_p1}")
        history_p2_resp = await ChatService.get_history(
            db_session=session,
            session_id=session_id,
            user_id=user_id,
            roles=["USER"],
            limit=50,
            cursor=cursor_p1
        )
        
        history_p2 = history_p2_resp.messages
        cursor_p2 = history_p2_resp.next_cursor
        print(f"Page 2 results: {len(history_p2)}")
        assert len(history_p2) == 10
        assert history_p2[0].content['text'] == "Message 059"
        assert history_p2[-1].content['text'] == "Message 050"
        assert cursor_p2 is None # No more messages
        
        print("✅ Keyset Pagination Verification Passed!")
        
        # Cleanup
        await session.execute(delete(ChatMessage).where(ChatMessage.user_id == user_id))
        await session.commit()

if __name__ == "__main__":
    asyncio.run(test_keyset_pagination())
