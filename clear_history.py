import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from backend.database.alchemy_config import alchemy_config

async def run():
    print("Clearing support_chat_history...")
    print(f"DB URL: {os.getenv('DATABASE_URL')}")
    try:
        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            await session.execute(text("DELETE FROM support_chat_history;"))
            await session.commit()
            print("Successfully cleared all chat history logs.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
