import asyncio
import sys
import os

# Add project root to path
sys.path.append('/home/lv/Desktop/fast-platform-core')

async def test_agent():
    try:
        from backend.services.commerce.barcode_agent import barcode_agent
        print("🔍 Testing BarcodeAgent...")
        res = await barcode_agent.verify("4968123159022", "Test Product", "Miccosmo")
        print("✅ Success!")
        print(res.json())
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent())
