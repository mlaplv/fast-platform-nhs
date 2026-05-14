import asyncio
import json
import os
import sys

# Add backend to path
sys.path.append(os.getcwd())

from backend.services.commerce.barcode_agent import barcode_agent

async def test_verify():
    barcode = "968123703603"
    product_name = "Miccosmo Hurry Harry Premium Neck Cream Rich"
    brand = "Thương hiệu quốc tế" # Simulate DB missing brand
    
    print(f"Testing BarcodeAgent for: {barcode} | {brand}")
    result = await barcode_agent.verify(barcode, product_name, brand)
    print("\nRESULT:")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_verify())
