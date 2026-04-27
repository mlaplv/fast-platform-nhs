import asyncio
from backend.services.commerce.price_agent import scan_product_price

async def test():
    print("🚀 [TEST] Triggering Price Agent for 'iPhone 15 Pro Max 256GB'...")
    try:
        result = await scan_product_price("iPhone 15 Pro Max 256GB")
        print("✅ [TEST] Success!")
        print(f"Analysis: {result.analysis_overview[:200]}...")
        print(f"Min Price: {result.min_market_price}")
    except Exception as e:
        print(f"❌ [TEST] Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
