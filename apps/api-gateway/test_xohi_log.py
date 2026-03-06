import asyncio
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.DEBUG)

async def run_test():
    # import inside the running loop
    from src.database.alchemy_config import alchemy_config
    from src.services.xohi_responder import xohi_responder
    
    engine = alchemy_config.get_engine()
    async with engine.begin() as conn:
        pass # initialize

    payload = {
        "id": "test-order-log-999",
        "ip": "1.1.1.1",
        "user_agent": "curl/7.68.0",
        "tenant_id": "default",
        "total_amount": 999000,
        "customer": "Test Attacker",
        # Simulating a cluster attack: multiple orders, same address, different IPs (already seeded previously)
        "phone": "0987654321", 
        "address": "123 Spam Street, Hacker City" 
    }
    
    print("Triggering handler...")
    await xohi_responder.handle_order_created(payload)
    print("Handler completed.")
    
    # Check DB
    async with alchemy_config.create_session_maker()() as session:
        res = await session.execute(text("SELECT id, message FROM notifications WHERE type='warning' OR type='critical' ORDER BY created_at DESC LIMIT 1"))
        print("\n=== LATEST NOTIFICATION ===")
        print(res.fetchone())
        
        res_chat = await session.execute(text("SELECT id, content FROM chat_messages WHERE session_id='account' ORDER BY created_at DESC LIMIT 1"))
        print("\n=== LATEST XOHI LOG ===")
        print(res_chat.fetchone())

if __name__ == "__main__":
    asyncio.run(run_test())
