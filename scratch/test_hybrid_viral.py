import asyncio
import httpx
import sys
import redis.asyncio as aioredis

BASE_URL = "https://api.osmo.vn/api/v1/client/viral"
PRODUCT_ID = "prod_miccosmo_virgin_white"
VOUCHER_ID = "VIRAL39K"

async def check_redis(label, token):
    r = aioredis.Redis(host="localhost", port=6379, db=0)
    keys = await r.keys("viral:*")
    print(f"[{label}] Redis Keys: {[k.decode() for k in keys]}")
    for k in keys:
        val = await r.get(k)
        ttl = await r.ttl(k)
        print(f"   Key: {k.decode()} | Val: {val.decode()[:15] if val else 'None'} | TTL: {ttl}s")
    await r.aclose()

async def run_test():
    print("=== STARTING VIRAL HYBRID FLOW DIAGNOSTIC ===")
    
    # 1. Issue Token
    print("\n[Step 1] Issuing share-intent token...")
    async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
        res = await client.post(f"{BASE_URL}/share-intent", json={"product_id": PRODUCT_ID})
        if res.status_code != 201:
            print(f"❌ Failed to issue token: {res.status_code} - {res.text}")
            sys.exit(1)
            
        data = res.json()
        token = data["token"]
        fingerprint = data["fingerprint"]
        print(f"✅ Token issued: {token[:16]}...")
        print(f"✅ Fingerprint: {fingerprint[:16]}...")
        
        await check_redis("After Step 1", token)
        
        # 2. Fast Closing Verification (share_duration_ms = 2000 < 4500) -> Must fail
        print("\n[Step 2] Sending verification with short duration telemetry (2000ms)...")
        payload_fast = {
            "product_id": PRODUCT_ID,
            "fingerprint": fingerprint,
            "token": token,
            "voucher_id": VOUCHER_ID,
            "telemetry": {
                "time_on_page_ms": 100,
                "share_duration_ms": 2000, # 2.0 seconds -> Too fast!
                "visibility_changes": 0,
                "scroll_depth_pct": 0.0,
                "interaction_count": 0,
                "share_method": "facebook",
                "popup_was_blocked": False,
                "mouse_acceleration": 0.0,
                "interaction_rhythm": 0.0,
                "honeypot_triggered": False
            }
        }
        res = await client.post(f"{BASE_URL}/verify-share", json=payload_fast)
        print(f"ℹ️ Status code: {res.status_code}")
        print(f"ℹ️ Response Text: {res.text}")
        
        await check_redis("After Step 2", token)
        
        # 3. Secure Verification with valid duration telemetry (5000ms) -> Must succeed
        print("\n[Step 3] Sending verification with valid duration telemetry (5000ms)...")
        payload_secure = {
            "product_id": PRODUCT_ID,
            "fingerprint": fingerprint,
            "token": token,
            "voucher_id": VOUCHER_ID,
            "telemetry": {
                "time_on_page_ms": 5000,
                "share_duration_ms": 5000, # 5.0 seconds -> Valid!
                "visibility_changes": 0,
                "scroll_depth_pct": 0.0,
                "interaction_count": 0,
                "share_method": "facebook",
                "popup_was_blocked": False,
                "mouse_acceleration": 0.0,
                "interaction_rhythm": 0.0,
                "honeypot_triggered": False
            }
        }
        res = await client.post(f"{BASE_URL}/verify-share", json=payload_secure)
        print(f"ℹ️ Status code: {res.status_code}")
        print(f"ℹ️ Response Text: {res.text}")
        
        await check_redis("After Step 3", token)

if __name__ == "__main__":
    asyncio.run(run_test())
