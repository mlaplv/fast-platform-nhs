import hmac
import hashlib
import time
import json
import asyncio
import os
import requests

async def run_real_a2a():
    from backend.database.dependencies import get_session
    from backend.database.models.commerce import ProductBase
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from backend.services.xohi_memory import xohi_memory

    # Whitelist the phone number in Redis to bypass anti-spam checks
    test_phone = "0987654321"
    if xohi_memory.client:
        print(f"🔓 Whitelisting phone number '{test_phone}' in Redis to bypass anti-spam...")
        await xohi_memory.client.sadd("spam:whitelist:phones", test_phone)

    print("🔎 Querying database for the Miccosmo Placenta Essence product...")
    async with get_session() as session:
        stmt = select(ProductBase).where(ProductBase.id == "prod_miccosmo_placenta_essence").options(selectinload(ProductBase.variants))
        res_db = await session.execute(stmt)
        prod = res_db.scalars().first()
        if not prod:
            # Fallback to any active product if specific product is not found
            stmt = select(ProductBase).where(ProductBase.status == "ACTIVE").limit(1).options(selectinload(ProductBase.variants))
            res_db = await session.execute(stmt)
            prod = res_db.scalars().first()
            
        if not prod:
            print("❌ No active product found in DB! Cannot test real checkout.")
            return

        product_id = prod.id
        price = int(prod.discount_price if prod.discount_price is not None else prod.price)
        print(f"✅ Target product: {prod.name} (ID: {product_id}) | Price: {price} VND")

    # Target agent key from environment configuration
    agent_key = os.getenv("AGENT_API_KEYS", "osmo-agent-secure-key-2026").split(",")[0].strip()
    api_url = "https://api.osmo.vn/api/v1/client/mcp/call"
    
    # SCENARIO 1: A2A Checkout WITHOUT voucher, shipping_fee = 30,000đ. Net Total: 525,000đ
    print("\n--- SCENARIO 1: A2A Checkout WITHOUT Voucher (Expected: 525.000₫) ---")
    payload_1 = {
        "name": "stealth_checkout",
        "arguments": {
            "items": [
                {
                    "product_id": product_id,
                    "variant_id": None,
                    "quantity": 1,
                    "price": price
                }
            ],
            "customer_name": "AI Real - Scenario A (No Voucher)",
            "customer_phone": test_phone,
            "customer_address": "123 Duong PII, Quan 1, TP. HCM, Viet Nam",
            "payment_method": "COD",
            "shipping_fee": 30000,
            "total_amount": price + 30000,
            "sandbox": False
        }
    }

    body_str_1 = json.dumps(payload_1, separators=(',', ':'))
    sig_1 = hmac.new(agent_key.encode("utf-8"), body_str_1.encode("utf-8"), hashlib.sha256).hexdigest()
    headers_1 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Agent-API-Key": agent_key,
        "X-Agent-Signature": sig_1,
        "X-Agent-Timestamp": str(time.time()),
        "Content-Type": "application/json"
    }

    try:
        response_1 = requests.post(api_url, data=body_str_1, headers=headers_1)
        print(f"Status Code: {response_1.status_code}")
        print(f"Response: {response_1.json()}")
    except Exception as e:
        print(f"❌ Scenario 1 failed: {e}")

    # SCENARIO 2: A2A Checkout WITH Voucher SALE30K, shipping_fee = 0đ. Net Total: 465,000đ
    print("\n--- SCENARIO 2: A2A Checkout WITH Voucher SALE30K (Expected: 465.000₫) ---")
    voucher_discount = 30000
    shipping_fee = 0
    payload_2 = {
        "name": "stealth_checkout",
        "arguments": {
            "items": [
                {
                    "product_id": product_id,
                    "variant_id": None,
                    "quantity": 1,
                    "price": price
                }
            ],
            "voucher_ids": ["SALE30K"],
            "customer_name": "AI Real - Scenario B (SALE30K)",
            "customer_phone": test_phone,
            "customer_address": "123 Duong PII, Quan 1, TP. HCM, Viet Nam",
            "payment_method": "COD",
            "shipping_fee": shipping_fee,
            "total_amount": price - voucher_discount + shipping_fee,
            "sandbox": False
        }
    }

    body_str_2 = json.dumps(payload_2, separators=(',', ':'))
    sig_2 = hmac.new(agent_key.encode("utf-8"), body_str_2.encode("utf-8"), hashlib.sha256).hexdigest()
    headers_2 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Agent-API-Key": agent_key,
        "X-Agent-Signature": sig_2,
        "X-Agent-Timestamp": str(time.time()),
        "Content-Type": "application/json"
    }

    try:
        response_2 = requests.post(api_url, data=body_str_2, headers=headers_2)
        print(f"Status Code: {response_2.status_code}")
        print(f"Response: {response_2.json()}")
    except Exception as e:
        print(f"❌ Scenario 2 failed: {e}")

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    asyncio.run(run_real_a2a())
