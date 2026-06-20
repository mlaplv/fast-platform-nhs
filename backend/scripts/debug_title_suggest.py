import os
import sys
import asyncio
from pathlib import Path

# Fix python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, ".env"))
except ImportError:
    pass

import logging
logging.basicConfig(level=logging.INFO)

from backend.database import async_session_maker
from backend.services.article_service import ArticleService

async def main():
    print("Testing ArticleService.suggest_titles...")
    async with async_session_maker() as session:
        service = ArticleService(vector_service=None)
        
        # Query any product first
        from backend.database.models import ProductBase
        from sqlalchemy import select
        prod_stmt = select(ProductBase).limit(1)
        prod = (await session.execute(prod_stmt)).scalars().first()
        product_id = ""
        if prod:
            product_id = prod.id
            print(f"Using product: {prod.name} (ID: {prod.id})")
        else:
            print("No product found in DB!")
        
        category = "Mỹ phẩm"
        keywords = "kem dưỡng cổ"
        
        print(f"Calling suggest_titles with: category={category}, keywords={keywords}, product_id={product_id}")
        try:
            titles = await service.suggest_titles(
                db_session=session,
                category=category,
                keywords=keywords,
                product_id=product_id
            )
            print("SUCCESS! Returned titles:")
            import pprint
            pprint.pprint(titles)
        except Exception as e:
            print("FAILED with exception:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
