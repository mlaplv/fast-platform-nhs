import sys
import asyncio
from lxml import html
sys.path.append('/home/lv/Desktop/fast-platform-core/backend')
from utils.noise_cleaner import noise_cleaner

async def test():
    text = '<p>Line 1<br>Line 2</p>'
    res = await noise_cleaner.clean(text, strip_html=False)
    print("Cleaned text:", repr(res))

asyncio.run(test())
