import asyncio
import os
from sqlalchemy import select

async def main():
    from backend.database.alchemy_config import alchemy_config
    from backend.database.models import User
    from backend.services.ai_service import ai_service
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    
    # Initialize trinity bridge
    await trinity_bridge.initialize()
    
    async with alchemy_config.create_session_maker()() as session:
        # Get first user (admin or standard)
        stmt = select(User).limit(1)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            print("No users found in database!")
            return
            
        print(f"Testing Auto-Optimize for User ID: {user.id}")
        
        # Run auto optimize stack
        res = await ai_service.auto_optimize_stack(session, user.id)
        
        print("\n--- AUTO-OPTIMIZE RESULT ---")
        print(f"Status: {res.ok}")
        print(f"Message: {res.message}")
        print(f"Data: {res.data}")

if __name__ == "__main__":
    asyncio.run(main())
