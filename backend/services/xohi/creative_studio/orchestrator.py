import os
import logging
import asyncio
from typing import Optional, Dict, Any
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.operatives.vision_insight import VisionInsight
from backend.services.xohi.creative_studio.operatives.asset_hunter import AssetHunter
from backend.services.xohi.creative_studio.operatives.creative_pen import CreativePen
from backend.services.xohi.creative_studio.operatives.plagiarism_cop import PlagiarismCop
from backend.services.xohi.creative_studio.formatters.media_compressor import MediaCompressor
from backend.services.xohi.creative_studio.registry import registry
from backend.constants.agentic import ORCHESTRATOR_SEMAPHORE_LIMIT
from backend.database.alchemy_config import alchemy_config
from backend.schemas.intent import IntentResponse

# Modular Handlers
from backend.services.xohi.creative_studio.handlers.voice import VoiceHandler
from backend.services.xohi.creative_studio.handlers.actions import ActionHandler
from backend.services.xohi.creative_studio.handlers.engine import ExecutionEngine

logger = logging.getLogger("api-gateway")

class ContentOrchestrator:
    """
    The brain of V62.1 Content Factory. 
    Coaches specialized agents and delegates request handling to domain handlers.
    """
    def __init__(self, vision=None, hunter=None, pen=None, cop=None, media=None):
        self.vision = vision or VisionInsight()
        self.pen = pen or CreativePen(model_name=os.getenv("TIER3_MODEL", "gemini-3.1-pro-preview-customtools"))
        self.cop = cop or PlagiarismCop()
        self.media = media or MediaCompressor()
        
        # AssetHunter config
        if not hunter:
            keys = []
            for i in ["", "_1", "_2"]:
                k, cx = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}"), os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
                if k and cx: keys.append({"key": k, "cx": cx})
            self.hunter = AssetHunter(keys)
        else:
            self.hunter = hunter
            
        self.semaphore = asyncio.Semaphore(ORCHESTRATOR_SEMAPHORE_LIMIT)
        
        # Step Registry
        registry.register(1, self.vision); registry.register(2, self.hunter)
        registry.register(3, self.pen); registry.register(4, self.pen)
        # Step 5 is now a pure Presentation/Certification Step (No automated AI assigned)
        registry.register(6, self.media)
        
        # Initialize Handlers
        self.voice_handler = VoiceHandler(self)
        self.action_handler = ActionHandler(self)
        self.engine = ExecutionEngine(self)
        
        logger.info("[Content Factory] Orchestrator initialized with lean modular handlers.")

    async def resume_all(self):
        """R104: Self-Healing Resume logic. R1.5: Zero-Hydration — only select needed columns."""
        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            from sqlalchemy import select, text
            stmt = select(ContentCampaign.id, ContentCampaign.current_step).where(
                ContentCampaign.status == "PROCESSING"
            )
            result = await session.execute(stmt)
            rows = result.all()
            for row in rows:
                asyncio.create_task(self.engine.trigger_step(row.id, force_step=row.current_step))

    # --- Delegated API Surface ---

    async def handle_voice_request(self, transcript: str, campaign_repo: ContentCampaignRepository, tenant_id: str = "default", user_id: str = None) -> IntentResponse:
        return await self.voice_handler.handle_request(transcript, campaign_repo, tenant_id, user_id)

    async def get_active_campaign(self, campaign_repo: ContentCampaignRepository, user_id: str = None, tenant_id: str = "default") -> Optional[ContentCampaign]:
        return await self.voice_handler.get_active_campaign(campaign_repo, user_id, tenant_id)

    async def approve_step(self, campaign_id: str, data: Dict[str, Any], campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        return await self.action_handler.approve_step(campaign_id, data, campaign_repo)

    async def retry_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        return await self.action_handler.retry_step(campaign_id, campaign_repo)

    async def update_metadata(self, campaign_id: str, data: Dict[str, Any], campaign_repo: ContentCampaignRepository) -> Dict[str, Any]:
        return await self.action_handler.update_metadata(campaign_id, data, campaign_repo)

    async def _trigger_next_step(self, campaign_id: str, force_step: int = None):
        await self.engine.trigger_step(campaign_id, force_step)

# Singleton
content_factory = ContentOrchestrator()
