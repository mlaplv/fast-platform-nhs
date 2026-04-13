import os
import sys
import asyncio
from pathlib import Path
from sqlalchemy import select, update
from dotenv import load_dotenv

# Setup project root for imports
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load env before other imports
load_dotenv(os.path.join(project_root, ".env"))

from backend.database import async_session_maker, engine
from backend.database.models import ProductBase, Article
from backend.utils.text import slugify

async def fix_data():
    # Elite V2.2: Dynamic Tenant Resolution
    # Match the logic in frontend/src/lib/server/env.ts
    target_tenant = os.getenv("APP_DOMAIN", "micsmo.com")
    print(f"🚀 Starting SAFE Migration: Setting Tenant ID to '{target_tenant}' and auto-generating slugs...")

    async with async_session_maker() as session:
        try:
            # 1. Update Products
            print("📦 Processing Products...")
            stmt = select(ProductBase)
            result = await session.execute(stmt)
            products = result.scalars().all()
            
            p_count = 0
            for p in products:
                old_slug = p.slug
                new_slug = slugify(p.name)
                
                # Update if tenant mismatch or slug mismatch
                if p.tenant_id != target_tenant or old_slug != new_slug:
                    p.tenant_id = target_tenant
                    p.slug = new_slug
                    p_count += 1
                    print(f"  [UPDATED] {p.name[:30]}... | Slug: {old_slug} -> {new_slug} | Tenant: {target_tenant}")

            # 2. Update Articles
            print("📰 Processing Articles...")
            stmt = select(Article)
            result = await session.execute(stmt)
            articles = result.scalars().all()
            
            a_count = 0
            for a in articles:
                old_slug = a.slug
                new_slug = slugify(a.title)
                
                if a.tenant_id != target_tenant or old_slug != new_slug:
                    a.tenant_id = target_tenant
                    a.slug = new_slug
                    a_count += 1
                    print(f"  [UPDATED] {a.title[:30]}... | Slug: {old_slug} -> {new_slug} | Tenant: {target_tenant}")

            await session.commit()
            print(f"✨ Success! Updated {p_count} products and {a_count} articles.")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_data())
