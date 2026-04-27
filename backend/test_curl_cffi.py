import asyncio
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
import re

async def main():
    url = "https://www.google.com/search?q=Miccosmo+Beppin+Body+Virgin+White+Serum&tbm=shop&hl=vi&gl=vn"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    async with AsyncSession(impersonate="chrome110") as s:
        resp = await s.get(url, headers=headers)
        if resp.status_code == 200:
            print("Length of HTML:", len(resp.text))
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.find_all('div', class_='sh-dgr__grid-result')
            if not items:
                items = soup.find_all('div', class_='sh-pr__product-results-grid')
            print(f"Found {len(items)} items.")
            
            prices = re.findall(r'[\d.,]+\s*&#8363;|[\d.,]+\s*đ', resp.text, re.IGNORECASE)
            print("Found raw prices in text:", len(prices))
            print(prices[:10])
        else:
            print(f"Failed with status: {resp.status_code}")

asyncio.run(main())
