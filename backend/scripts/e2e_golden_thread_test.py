import asyncio
import os
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.orm.attributes import flag_modified

# Load environment
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from backend.database.alchemy_config import alchemy_config
from backend.database.models import ContentCampaign, User
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.orchestrator import content_factory
from backend.services.xohi.creative_studio.registry import registry
from backend.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor

# Redirect Step 6 to a writable directory for E2E validation
test_upload_dir = "test_static/uploads/v62"
os.makedirs(test_upload_dir, exist_ok=True)
test_media = MediaCompressor(upload_dir=test_upload_dir)
registry.register(6, test_media)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("E2E_GOLDEN_THREAD")

async def run_e2e_test():
    logger.info("=== STARTING E2E GOLDEN THREAD VALIDATION ===")

    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        repo = ContentCampaignRepository(session=session)

        # 1. Create a fresh campaign
        campaign_id = str(uuid.uuid4())
        campaign = ContentCampaign(
            id=campaign_id,
            user_id="user_admin",
            source_input="Tầm quan trọng của AI trong năm 2026",
            status="PROCESSING",
            current_step=1,
            tenant_id="smartshop"
        )
        session.add(campaign)
        await session.commit()

        logger.info(f"Created Campaign: {campaign_id}")

        # Helper to refresh campaign
        async def refresh():
            nonlocal campaign
            # Explicitly refresh deferred columns to avoid MissingGreenlet
            await session.refresh(campaign, ["final_html"])
            from sqlalchemy import select
            stmt = select(ContentCampaign).where(ContentCampaign.id == campaign_id)
            result = await session.execute(stmt)
            campaign = result.scalar_one()

        # Step 1: Topic Research
        logger.info("--- Step 1: Topic Research ---")
        op1 = registry.get_operative(1)
        resp1 = await op1.execute(campaign_id, repo, step=1)
        campaign.topic_data = resp1.data
        campaign.gold_metadata = resp1.data # Seed initial metadata
        await repo.update(campaign)
        await session.commit()
        await refresh()
        logger.info(f"Step 1 Complete. Primary Keyword: {campaign.gold_metadata.get('primary_keyword')}")

        # Step 2: Asset Hunting (Crucial for seeding original URLs)
        logger.info("--- Step 2: Asset Hunting ---")
        op2 = registry.get_operative(2)
        resp2 = await op2.execute(campaign_id, repo, step=2)
        # Note: AssetHunter updates the campaign inside execute() and returns AgentResponse
        await refresh()
        orig_assets = campaign.get_gold_val("original_remote_assets")
        logger.info(f"Step 2 Complete. Original Assets Seeded: {len(orig_assets) if orig_assets else 0}")
        if not orig_assets:
            logger.error("FAIL: original_remote_assets NOT found in gold_metadata!")
            return

        # Step 3: Outlining
        logger.info("--- Step 3: Outlining ---")
        op3 = registry.get_operative(3)
        resp3 = await op3.execute(campaign_id, repo, step=3)
        campaign.outline_data = resp3.data.get("outline", resp3.data)
        # Simulate orchestrator logic: sync gold_metadata if returned
        if resp3.data and "gold_metadata" in resp3.data:
            campaign.gold_metadata = resp3.data["gold_metadata"]
        await repo.update(campaign)
        await session.commit()
        await refresh()

        # Step 4: Creative Writing
        logger.info("--- Step 4: Creative Writing ---")
        op4 = registry.get_operative(4)
        resp4 = await op4.execute(campaign_id, repo, step=4)
        campaign.draft_content = resp4.data.get("content", campaign.draft_content)
        await repo.update(campaign)
        await session.commit()
        await refresh()
        logger.info("Step 4 Complete. Content generated.")

        # Step 5: Plagiarism Check (Verify it doesn't drop original_remote_assets)
        logger.info("--- Step 5: Plagiarism Check ---")
        op5 = registry.get_operative(5)
        resp5 = await op5.execute(campaign_id, repo, step=5)
        await refresh()
        orig_assets_after_5 = campaign.get_gold_val("original_remote_assets")
        logger.info(f"Step 5 Complete. Original Assets still present: {len(orig_assets_after_5) if orig_assets_after_5 else 0}")
        if not orig_assets_after_5:
            logger.error("FAIL: original_remote_assets DROPPED in Step 5!")
            return

        # Step 6: Media Localization (The Final Test)
        logger.info("--- Step 6: Media Localization ---")
        op6 = registry.get_operative(6)
        logger.info(f"Draft content before Step 6: {campaign.draft_content[:50] if campaign.draft_content else 'NONE'}")
        resp6 = await op6.execute(campaign_id, repo, step=6)
        logger.info(f"Step 6 response message: {resp6.message}")

        # Explicitly sync results to campaign object as orchestrator would
        if resp6.data:
            if "final_html" in resp6.data:
                logger.info(f"Syncing final_html (length: {len(resp6.data['final_html']) if resp6.data['final_html'] else 'NONE'})")
                campaign.final_html = resp6.data["final_html"]
            if "assets" in resp6.data:
                campaign.assets_data = resp6.data["assets"]

        await repo.update(campaign)
        await session.commit()
        await refresh()

        final_html = campaign.final_html
        logger.info(f"Final HTML after refresh: {final_html[:50] if final_html else 'NONE'}")
        local_assets = campaign.assets_data

        logger.info(f"Step 6 Complete. Local Assets: {len(local_assets)}")

        # Verify Replacement
        found_remote = False
        for url in orig_assets:
            if url in final_html:
                found_remote = True
                logger.error(f"FAIL: Remote URL still found in final_html: {url}")

        found_local = False
        for path in local_assets:
            if path in final_html:
                found_local = True

        if not found_remote and found_local:
            logger.info("SUCCESS: All remote URLs replaced with local paths in final_html!")
        elif found_remote:
            logger.error("FAIL: Replacement incomplete.")
        else:
            logger.warning("WARN: No local paths found in final_html (maybe no placeholders were used?)")

    logger.info("=== E2E TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
