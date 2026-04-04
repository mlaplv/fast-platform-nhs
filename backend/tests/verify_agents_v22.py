import asyncio
import os
import json
import httpx
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# 2. Path setup
PROJECT_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

# 3. Load .env and IMMEDIATELY OVERRIDE (for host-based test script)
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# Ensure host-based execution connects to localhost instead of Docker hostnames
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["DB_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_platform"
os.environ["DATABASE_URL"] = os.environ["DB_URL"]

# 4. HELEN API CONFIG
BASE_URL = os.getenv("API_URL", "http://localhost:8000")

async def test_helen_lead_extraction():
    """TEST 2: Helen Support Agent - Purchase Intent Extraction."""
    print("\n" + "="*60)
    print("🚀 [HELEN TEST] Simulated Purchase Intent")
    print("="*60)
    
    url = f"{BASE_URL}/api/v1/client/support/chat"
    payload = {
        "message": "cho tôi 1 lọ thuốc đặc trị hôi nách về địa chỉ 336/44 nguyễn văn luông phú lâm, 0949901122, lập",
        "session_id": f"test_helen_{int(datetime.now().timestamp())}",
        "product_slug": "hoi-nach-helen"
    }
    
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        try:
            print(f"Sending message: {payload['message']}")
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            
            if response.status_code in [200, 202]:
                data = response.json()
                print(f"Reply: {data.get('reply')}")
                print(f"Task ID: {data.get('task_id')}")
                
                # Check for direct extraction if it's sync
                if data.get("status") == "DONE":
                    print("✅ Extraction completed synchronously.")
                else:
                    print(f"⏳ Task is processing... Task ID: {data.get('task_id')}")
            else:
                print(f"❌ Error: {response.text}")
        except Exception as e:
            print(f"❌ Helen Test Failed: {e}")

async def test_xohi_scout():
    """TEST 1: XoHi Content Factory - Neural Scout (Step 1)."""
    print("\n" + "="*60)
    print("🚀 [XOHI TEST] Neural Scout for Content Generation")
    print("="*60)
    
    # Deferred imports to ensure os.environ["REDIS_URL"] is respected
    from backend.services.xohi.creative_studio.orchestrator import content_factory
    from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
    
    # CNS V82.50: Must initialize AI Bridge in standalone scripts
    print("📡 Initializing Neural Bridge (TrinityBridge)...")
    await trinity_bridge.initialize()
    
    topic = "trị hôi nách hồng sơn"
    print(f"Topic: {topic}")
    
    try:
        # We call the analyst.scout directly to verify the research engine
        result = await content_factory.analyst.scout(topic)
        
        if result.status == "success":
            report = result.data
            print("✅ Scout Report Generated Successfully!")
            print(f"Topic: {report.get('topic')}")
            print(f"Headlines found: {len(report.get('headlines', []))}")
            if report.get('headlines'):
                print(f"Sample Headline: {report['headlines'][0]['title']}")
            print(f"Keywords: {', '.join(report.get('semantic_keywords', [])[:5])}...")
            
            # Print strategic notes
            analysis = report.get('strategic_analysis', '')
            print(f"Strategic Analysis Snippet: {analysis[:200]}...")
        else:
            print(f"❌ XoHi Scout Failed: {result.message}")
            
    except Exception as e:
        print(f"❌ XoHi Test Exception: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("🔥🔥 STARTING ELITE V2.2 AGENT VERIFICATION 🔥🔥")
    
    # Run XoHi First (Internal service call)
    await test_xohi_scout()
    
    # Run Helen (API call)
    await test_helen_lead_extraction()
    
    print("\n" + "="*60)
    print("✅ VERIFICATION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
