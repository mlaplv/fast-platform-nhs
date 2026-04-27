import asyncio
import json
from backend.services.xohi.google_search import google_search_service

async def main():
    query = "Miccosmo Beppin Body Virgin White Serum mua online giá site:shopee.vn OR site:lazada.vn OR site:tiki.vn OR site:hasaki.vn"
    results = await google_search_service.search(query, num=10)
    for i, r in enumerate(results):
        print(f"{i+1}. {r.get('title')}")
        print(f"   Link: {r.get('link')}")

asyncio.run(main())
