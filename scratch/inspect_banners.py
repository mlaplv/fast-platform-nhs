import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import json

async def run():
    for host in ["localhost", "db"]:
        try:
            engine = create_async_engine(f'postgresql+asyncpg://postgres:postgres@{host}:5432/fast_platform')
            async with engine.connect() as conn:
                res = await conn.execute(text("SELECT id, title, position, image_url, mobile_image_url, link_url, is_active FROM banners"))
                rows = res.fetchall()
                if rows:
                    for row in rows:
                        print(f"ID: {row[0]} | Title: {row[1]} | Position: {row[2]} | Image: {row[3]} | MobileImage: {row[4]} | Link: {row[5]} | Active: {row[6]}")
                else:
                    print("No banners found in database")
            await engine.dispose()
            return
        except Exception as e:
            print(f"Failed {host}: {e}")
            continue

if __name__ == "__main__":
    asyncio.run(run())
