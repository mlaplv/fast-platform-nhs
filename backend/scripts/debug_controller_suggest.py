import os
import sys
import asyncio
from pathlib import Path

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

async def run_test(product_id_value, desc):
    print("\n" + "="*50)
    print(f"TESTING WITH: {desc} (product_id = {repr(product_id_value)})")
    print("="*50)
    async with async_session_maker() as session:
        service = ArticleService(vector_service=None)
        try:
            titles = await service.suggest_titles(
                db_session=session,
                category="Mỹ phẩm",
                keywords="kem dưỡng cổ",
                product_id=product_id_value
            )
            print("SUCCESS! Returned titles:")
            import pprint
            pprint.pprint(titles)
        except Exception as e:
            print("FAILED with exception:")
            import traceback
            traceback.print_exc()

async def main():
    # Test 1: Empty string
    await run_test("", "Empty String")
    
    # Test 2: Malformed UUID (e.g., 'null' or 'undefined' from frontend)
    await run_test("null", "Malformed UUID 'null'")
    await run_test("undefined", "Malformed UUID 'undefined'")
    await run_test("123-abc", "Malformed UUID '123-abc'")

if __name__ == "__main__":
    asyncio.run(main())
