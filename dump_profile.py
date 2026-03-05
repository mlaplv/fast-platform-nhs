
import asyncio
import os
import sys

# Add the specific app src to path
sys.path.append("/app/apps/api-gateway")

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv

# Set up environment
load_dotenv("/app/.env")

from src.database import async_session_maker
from src.database.models import User, VoiceProfile

async def dump_profile():
    async with async_session_maker() as session:
        stmt = select(User).where(User.email == "admin@smartshop.test").options(
            selectinload(User.voice_profile)
        )
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        
        if not user:
            print("User not found")
            return
            
        profile = user.voice_profile
        if not profile:
            print("No voice profile found for user")
            return
            
        print(f"User ID: {user.id}")
        print(f"Wake Words: {profile.wake_words}")
        print(f"Sleep Words: {profile.sleep_words}")
        print(f"Greeting Template: {profile.greeting_template}")

if __name__ == "__main__":
    asyncio.run(dump_profile())
