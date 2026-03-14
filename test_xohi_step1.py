import asyncio
import os
import json
import logging
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.database.repositories import ContentCampaignRepository
from backend.database.alchemy_config import alchemy_config
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.ai_engine.core.key_rotator import key_rotator

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

async def run_step_1():
    print("⚙️ Initializing AI Infrastructure...")
    await trinity_bridge.initialize()
    await key_rotator.load_keys()

    print(f"🔑 Keys loaded in Rotator: {key_rotator.get_count()}")
    if key_rotator.get_count() == 0:
        print("❌ ERROR: No keys loaded. Check DB/ENV.")
        # Try to force reload or check DB directly
        from backend.database.models import VoiceProfile
        from sqlalchemy import select
        async with alchemy_config.create_session_maker()() as session:
            stmt = select(VoiceProfile)
            res = await session.execute(stmt)
            profiles = res.scalars().all()
            print(f"📊 Profiles in DB: {len(profiles)}")
            for p in profiles:
                print(f"  - Profile ID: {p.id}, Keys Encrypted: {bool(p.gemini_keys_enc)}")

    # Phase 2: Setup Repo and Session
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        repo = ContentCampaignRepository(session=session)
        transcript = "Thời trang nam cao cấp"

        print(f"--- [STARTING STEP 1: VISION INSIGHT] ---")
        response = await content_factory.handle_voice_request(transcript, repo)

        output = {
            "status": response.status,
            "message": response.message,
            "data": response.data
        }

        keywords = output["data"].get("keywords", {})
        title = keywords.get("title", "")
        is_fallback = "Khám phá" in title and "Xohi AI Strategy" in str(output["data"])

        print(f"Result Type: {'⚠️ FALLBACK' if is_fallback else '✅ REAL AI'}")
        print(json.dumps(output, indent=2, ensure_ascii=False))

        return output["data"].get("campaign_id")

if __name__ == "__main__":
    asyncio.run(run_step_1())
