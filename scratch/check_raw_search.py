import sys
import os
import asyncio
import json

# Add backend to path
sys.path.append(os.getcwd())

from backend.services.xohi.google_search import google_search_service

async def check():
    query = "Miccosmo Beppin Body Virgin White Serum giá bán"
    print(f"Searching for: {query}")
    results = await google_search_service.search(query, num=10)
    
    for i, r in enumerate(results):
        print(f"[{i+1}] {r['title']}")
        print(f"    Link: {r['link']}")
        print(f"    Snippet: {r.get('snippet', '')}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check())
