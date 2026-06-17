import asyncio
from backend.database.dependencies import get_session
from backend.database.models.commerce import ProductBase
from sqlalchemy import select

async def main():
    async with get_session() as session:
        stmt = select(ProductBase).where(ProductBase.status == "ACTIVE")
        res = await session.execute(stmt)
        products = res.scalars().all()
        print(f"Total active products: {len(products)}")
        for p in products:
            meta = p.product_metadata or {}
            video_url = meta.get("video_url")
            images = p.images or []
            
            # Check if any media path looks like a video or if video_url is present
            has_video = video_url or any(
                any(str(m).lower().endswith(ext) for ext in (".mp4", ".webm", ".mov", ".avi"))
                for m in images
            )
            
            if has_video:
                print(f"Product: {p.name}")
                print(f"  SKU: {p.sku}")
                print(f"  Metadata video_url: {video_url}")
                print(f"  Images: {images}")
                print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
