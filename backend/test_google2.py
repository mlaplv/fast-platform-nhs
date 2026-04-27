import asyncio
import json
from backend.services.xohi.google_search import google_search_service

async def main():
    query = "Miccosmo Beppin Body Virgin White Serum giá"
    results = await google_search_service.search(query, num=10)
    print("Found", len(results))
    for r in results:
        print(json.dumps(r, indent=2, ensure_ascii=False))

asyncio.run(main())
