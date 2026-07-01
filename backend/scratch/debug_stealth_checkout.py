import asyncio
import hmac
import hashlib
import time
import json
import httpx
from backend.database.dependencies import get_session
from backend.database.models.commerce import ProductBase
from sqlalchemy import select

async def main():
    async with get_session() as session:
        # Get the product
        stmt = select(ProductBase).where(ProductBase.id == "prod_miccosmo_virgin_white")
        res_db = await session.execute(stmt)
        prod = res_db.scalars().first()
        if not prod:
            print("Product prod_miccosmo_virgin_white not found in database!")
            return
        
        product_id = prod.id
        price = int(prod.price)
        print(f"Using product: {prod.name} ({product_id}), price: {price}")

    agent_key = "osmo-agent-secure-key-2026"
    payload = {
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
            "customer_name": "Nguyen Van A Sandbox",
            "customer_phone": "0988665544",
            "customer_address": "Hà Nội",
            "total_amount": price,
            "sandbox": True
        }
    }
    
    body_str = json.dumps(payload, separators=(',', ':'))
    now = str(time.time())
    sig = hmac.new(agent_key.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()
    
    headers = {
        "User-Agent": "headless-python-requests/2.31.0",
        "X-Agent-API-Key": agent_key,
        "X-Agent-Signature": sig,
        "X-Agent-Timestamp": now,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Since the server runs on localhost:8000 (api service mapped in docker compose)
        response = await client.post("http://api:8000/api/v1/client/mcp/call", content=body_str, headers=headers, timeout=10.0)
        print("Response code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except Exception:
            print("Response Text:", response.text)

if __name__ == "__main__":
    asyncio.run(main())
