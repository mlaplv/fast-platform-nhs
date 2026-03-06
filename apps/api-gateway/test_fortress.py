import asyncio
import logging
from src.services.anti_spam import anti_spam_service

logging.basicConfig(level=logging.INFO)

async def test_botnet_race_condition():
    print("\n--- TEST 1: BOTNET RACE CONDITION (Atomic Lua Test) ---")
    
    # 50 concurrent requests from same IP/Address but we want to see if Rapid Fire catches them properly
    # Using same fingerprint
    ip = "2.2.2.2"
    ua = "Botnet/1.0"
    tenant = "default"
    data = {"phone": "0911111111", "address": "Botnet HQ"}
    
    async def fire_req():
        return await anti_spam_service.check_order_spam(ip, ua, tenant, data)
        
    results = await asyncio.gather(*[fire_req() for _ in range(20)])
    
    spam_count = sum(1 for r in results if r[0])
    print(f"Total Requests: 20")
    print(f"Blocked as SPAM: {spam_count}")
    print(f"Sample Last Result: Score={results[-1][2]}, Reason={results[-1][1]}")

async def test_dorm_office_fp():
    print("\n--- TEST 2: DORM/OFFICE FALSE POSITIVE (Trust Bonus Test) ---")
    
    # Simulate an office where 5 different people order to the same building
    address = "Vincom Center Landmark 81"
    tenant = "default"
    
    for i in range(5):
        ip = f"192.168.1.{i}"
        ua = f"OfficeWorker/{i}.0"
        phone = f"093333333{i}"
        
        is_spam, reason, score, fp = await anti_spam_service.check_order_spam(
            ip, ua, tenant, {"phone": phone, "address": address}
        )
        print(f"Worker {i}: SPAM={is_spam}, Score={score}, Reason={reason}")

async def run_all():
    # Hack to initialize the redis client connection properly 
    from src.database.alchemy_config import alchemy_config
    engine = alchemy_config.get_engine()
    async with engine.begin() as conn:
        pass 
        
    # Must wait for redis to be actually connected in xohi_memory init
    await asyncio.sleep(1)
    
    # clear redis keys for clean test
    await anti_spam_service.redis.flushdb()
    
    await test_botnet_race_condition()
    await test_dorm_office_fp()

if __name__ == "__main__":
    asyncio.run(run_all())
