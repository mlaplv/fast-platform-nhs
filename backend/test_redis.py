import asyncio
import redis.asyncio as redis
import time

async def test():
    r = redis.from_url('redis://redis:6379/0')
    p = r.pubsub()
    await p.subscribe('test')
    t0 = time.time()
    for _ in range(5):
        msg = await p.get_message(ignore_subscribe_messages=True, timeout=15.0)
        print(f'Msg: {msg}, Time elapsed: {time.time() - t0:.2f}s')

if __name__ == "__main__":
    asyncio.run(test())
