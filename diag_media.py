import asyncio
from sqlalchemy import select
from backend.database import alchemy_config
from backend.database.models import ProductBase, MediaRegistry
from backend.utils.media import extract_media_urls

async def diag():
    m = alchemy_config.create_session_maker()
    async with m() as s:
        p = await s.get(ProductBase, 'prod_hoi_nach_hong_son')
        if not p:
            print("Product NOT FOUND")
            return
            
        print(f"--- PRODUCT DIAGNOSTIC ---")
        print(f"Base Images: {p.images}")
        print(f"Mobile Images: {p.mobile_images}")
        print(f"Tier Variations: {p.tier_variations}")
        
        # Test extraction
        data = {
            "images": p.images,
            "mobile_images": p.mobile_images,
            "tier_variations": p.tier_variations
        }
        extracted = extract_media_urls(data)
        print(f"Extracted URLs: {list(extracted)}")
        
        # Check Media Registry
        print(f"\n--- MEDIA REGISTRY (TOP 20) ---")
        stmt = select(MediaRegistry).limit(20)
        res = await s.execute(stmt)
        for m_row in res.scalars().all():
            print(f"ID: {m_row.id} | Path: {m_row.file_path} | linked: {m_row.is_linked}")
            
        # Match test
        # Normalize extracted as MediaService does
        normalized = []
        for url in extracted:
            path = url.split("?")[0]
            if "/storage/" in path: path = path.split("/storage/")[-1]
            elif "/uploads/" in path: path = path.split("/uploads/")[-1]
            normalized.append(path.strip("/"))
        
        print(f"\n--- MATCHING TEST ---")
        print(f"Normalized Paths for query: {normalized}")
        
        stmt_match = select(MediaRegistry.id).where(MediaRegistry.file_path.in_(normalized))
        matches = (await s.execute(stmt_match)).scalars().all()
        print(f"MATCHES FOUND: {matches}")

if __name__ == "__main__":
    import os
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
    asyncio.run(diag())
