import asyncio
import httpx
import re

async def main():
    url = "https://www.google.com/search?q=Miccosmo+Beppin+Body+Virgin+White+Serum&tbm=shop&hl=vi&gl=vn"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        with open("/tmp/google.html", "w") as f:
            f.write(resp.text)
        print("Length of HTML:", len(resp.text))

asyncio.run(main())
