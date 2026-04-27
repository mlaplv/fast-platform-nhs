import asyncio
import httpx
import re

async def main():
    url = "https://www.google.com/search?q=Miccosmo+Beppin+Body+Virgin+White+Serum&tbm=shop&hl=vi&gl=vn"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            print("Success! Checking HTML...")
            prices = re.findall(r'[\d.,]+&#8363;|[\d.,]+\s*đ', resp.text, re.IGNORECASE)
            print("Found prices:", prices[:10])
        else:
            print(f"Failed with status: {resp.status_code}")

asyncio.run(main())
