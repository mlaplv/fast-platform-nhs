
import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load .env from the root directory
load_dotenv("/home/lv/Desktop/fast-platform-core/.env")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# If running on local machine and 'db' host is not reachable, try localhost
if "db:5432" in DATABASE_URL:
    # Try localhost instead
    DATABASE_URL = DATABASE_URL.replace("db:5432", "localhost:5432")

async def check_db():
    print(f"Connecting to: {DATABASE_URL}")
    try:
        engine = create_async_engine(DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            print("Successfully connected to DB.")
            
            try:
                # Check for unaccent extension
                res = await session.execute(text("SELECT unaccent('hành');"))
                print(f"✅ Unaccent check: {res.scalar()}")
            except Exception as e:
                print(f"❌ Unaccent check failed: {e}")
                
            try:
                # Check for pgvector extension
                res = await session.execute(text("SELECT '[1,2,3]'::vector;"))
                print(f"✅ Vector check: {res.scalar()}")
            except Exception as e:
                print(f"❌ Vector check failed: {e}")

            try:
                # Check product count
                res = await session.execute(text("SELECT count(*) FROM product_bases;"))
                print(f"📦 Product count: {res.scalar()}")
            except Exception as e:
                print(f"❌ Product count check failed: {e}")

            try:
                # Check if any products have embeddings
                res = await session.execute(text("SELECT count(*) FROM product_embeddings;"))
                print(f"🧠 Embedding count: {res.scalar()}")
            except Exception as e:
                print(f"❌ Embedding count check failed: {e}")

    except Exception as e:
        print(f"CRITICAL: Failed to connect to DB: {e}")
    finally:
        if 'engine' in locals():
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_db())
