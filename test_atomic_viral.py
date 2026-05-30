import asyncio
import os
import sys
from pathlib import Path
import httpx

# Add parent path to allow backend imports
sys.path.append(str(Path(__file__).parent))

BASE_URL = "https://api.osmo.vn/api/v1/client/viral"
PRODUCT_ID = "prod_miccosmo_virgin_white"
VOUCHER_ID = "VIRAL39K"

async def run_test():
    print("=== STARTING VIRAL ATOMIC FLOW DIAGNOSTIC ===")
    
    # 1. Issue Token
    print("\n[Step 1] Issuing share-intent token...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(f"{BASE_URL}/share-intent", json={"product_id": PRODUCT_ID})
        if res.status_code != 201:
            print(f"❌ Failed to issue token: {res.status_code} - {res.text}")
            sys.exit(1)
            
        data = res.json()
        token = data["token"]
        fingerprint = data["fingerprint"]
        print(f"✅ Token issued: {token[:16]}...")
        print(f"✅ Fingerprint: {fingerprint[:16]}...")
        
        # 2. Premature Verification (Must fail but NOT delete token)
        print("\n[Step 2] Sending premature verification (no OAuth callback yet)...")
        payload = {
            "product_id": PRODUCT_ID,
            "fingerprint": fingerprint,
            "token": token,
            "voucher_id": VOUCHER_ID,
            "telemetry": None
        }
        res = await client.post(f"{BASE_URL}/verify-share", json=payload)
        print(f"ℹ️ Status code: {res.status_code}")
        print(f"ℹ️ Text: {res.json().get('detail') if res.status_code == 400 else res.text}")
        if res.status_code != 400:
            print("❌ Error: Premature verification should have failed with 400!")
            sys.exit(1)
        print("✅ Passed: Verification rejected as expected.")
        
        # 3. Second Premature Verification (Should still exist and fail with 400 - NOT expired/not found)
        print("\n[Step 3] Sending second premature verification to ensure token is still intact in Redis...")
        res = await client.post(f"{BASE_URL}/verify-share", json=payload)
        print(f"ℹ️ Status code: {res.status_code}")
        print(f"ℹ️ Text: {res.json().get('detail') if res.status_code == 400 else res.text}")
        if res.status_code != 400:
            print("❌ Error: Second premature verification should have failed with 400!")
            sys.exit(1)
        print("✅ Passed: Token still exists and is rejected as expected.")
        
        # 4. Trigger Webhook Callback directly in Redis
        print("\n[Step 4] Triggering simulated OAuth verification directly in Redis...")
        from backend.services.viral_share_service import viral_share_service
        # Initialize Redis connection if needed
        if not viral_share_service._redis:
            # Fallback direct connection
            import redis.asyncio as aioredis
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            r = aioredis.Redis(host=redis_host, port=redis_port, db=0)
            await r.set(f"viral:verified:{token}", "1", ex=600)
            await r.close()
        else:
            await viral_share_service.mark_token_verified(token)
            
        print("✅ Redis state successfully marked as VERIFIED.")
        
        # 5. Successful Verification (Must succeed)
        print("\n[Step 5] Sending verification after Webhook Callback...")
        res = await client.post(f"{BASE_URL}/verify-share", json=payload)
        print(f"ℹ️ Status code: {res.status_code}")
        if res.status_code != 201 and res.status_code != 200:
            print(f"❌ Failed successful verification: {res.text}")
            sys.exit(1)
        print("✅ Verification succeeded!")
        print(f"🎁 Voucher earned: {res.json()}")
        
        # 6. Replay Verification (Must fail immediately - Replay Proof)
        print("\n[Step 6] Sending replay verification to ensure OTT consumption...")
        res = await client.post(f"{BASE_URL}/verify-share", json=payload)
        print(f"ℹ️ Status code: {res.status_code}")
        print(f"ℹ️ Text: {res.json().get('detail') if res.status_code == 400 else res.text}")
        if res.status_code != 400:
            print("❌ Error: Replay verification should have failed with 400!")
            sys.exit(1)
        print("✅ Passed: Replay verification rejected. OTP successfully consumed!")

if __name__ == "__main__":
    asyncio.run(run_test())
