import asyncio
import os
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv

# R38: Ensure .env is loaded BEFORE any database imports
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from backend.database.models import Base, ContentCampaign, User
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.orchestrator import ContentOrchestrator
from backend.database.alchemy_config import alchemy_config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("battle_test_v61")

async def test_full_flow():
    logger.info(f"Using DB URL: {os.getenv('DATABASE_URL')}")
    logger.info("=== STARTING V61.1 BATTLE TEST: AGENTIC PIPELINE ===")
    
    # 1. Initialize DB Session
    session_maker = alchemy_config.create_session_maker()
    async with session_maker() as session:
        # Ensure user exists for FK
        res = await session.execute(select(User).where(User.id == "test_user"))
        if not res.scalar_one_or_none():
            logger.info("Provisioning 'test_user' for foreign key compliance...")
            test_user = User(
                id="test_user",
                username="test_user",
                email="test@smartshop.test",
                name="Test Professional",
                status="ACTIVE",
                tenant_id="test_tenant"
            )
            session.add(test_user)
            await session.commit()

        repo = ContentCampaignRepository(session=session)
        orchestrator = ContentOrchestrator()
        
        # 2. Trigger Step 1: Analyze Input
        logger.info("[Step 1] Initializing voice request...")
        prompt = "Viết bài về lợi ích của cà phê Arabica đối với sức khỏe"
        response = await orchestrator.handle_voice_request(
            transcript=prompt,
            campaign_repo=repo,
            tenant_id="test_tenant",
            user_id="test_user"
        )
        
        campaign_id = response.data.get("campaign_id")
        logger.info(f"Campaign Created: {campaign_id}")
        logger.info(f"AI Message: {response.message}")
        
        # 3. Simulate Approval for Step 1 -> Step 2
        logger.info("[Action] Simulating user approval...")
        approval_res = await orchestrator.approve_step(
            campaign_id=campaign_id,
            data={"approved": True, "step": 1},
            campaign_repo=repo
        )
        logger.info(f"Approval Response: {approval_res.get('message')}")
        
        # 4. Wait for Background Processing Group (Step 2 - 6)
        # We'll monitor the campaign status
        logger.info("Monitoring background progress (Polling every 3s)...")
        for i in range(15): # Max 45s wait
            await asyncio.sleep(3)
            # Re-fetch campaign
            campaign = await repo.get(campaign_id)
            logger.info(f"Iteration {i+1}: Step {campaign.current_step} | Status: {campaign.status}")
            
            if campaign.status == "WAITING_FOR_REVIEW":
                logger.info(f"Reached Step {campaign.current_step} - Waiting for approval.")
                # Auto-approve to keep the test moving
                await orchestrator.approve_step(campaign_id, {"approved": True, "step": campaign.current_step}, repo)
            
            if campaign.status == "COMPLETED":
                logger.info("🎉 CAMPAIGN COMPLETED SUCCESSFULLY!")
                break
        
        # Final check
        final_campaign = await repo.get(campaign_id)
        if final_campaign.status == "COMPLETED":
            logger.info("=== BATTLE TEST SUCCESSFUL ===")
            logger.info(f"Final Content Preview: {(final_campaign.draft_content or '')[:200]}...")
        else:
            logger.error(f"Test Timeout or Failed. Final Status: {final_campaign.status}")

if __name__ == "__main__":
    # Ensure environment variables load from project root
    from dotenv import load_dotenv
    from pathlib import Path
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    asyncio.run(test_full_flow())
