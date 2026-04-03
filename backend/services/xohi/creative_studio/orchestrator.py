from __future__ import annotations
import os
import logging
import asyncio
from sqlalchemy import select, text
from typing import Optional, Dict, Union, List
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
from backend.models.schemas import GenericResponse, AgentResponse

# Modular Handlers
from backend.services.xohi.creative_studio.handlers.voice import VoiceHandler
from backend.services.xohi.creative_studio.handlers.actions import ActionHandler
from backend.services.xohi.creative_studio.handlers.engine import ExecutionEngine
from backend.services.xohi.creative_studio.handlers.analyst import AnalystHandler
from backend.services.xohi.creative_studio.handlers.management import ManagementHandler
from backend.services.xohi.creative_studio.operatives.discovery_hunter import DiscoveryHunter
from backend.utils.config import get_env_json

logger = logging.getLogger("api-gateway")

class ContentOrchestrator:
    """
    The brain of V62.1 Content Factory. 
    Coaches specialized agents and delegates request handling to domain handlers.
    """
    def __init__(self, vision=None, hunter=None, pen=None, cop=None, media=None):
        keys = []
        # Elite V2.2: Standardized JSON Array (Keys + CXs rotation)
        env_keys = get_env_json("GOOGLE_SEARCH_KEYS")
        env_cxs = get_env_json("GOOGLE_SEARCH_CXS")
        
        # Priority 1: Paired JSON Arrays (V82.36 Standard)
        if env_keys and env_cxs:
            for i, k in enumerate(env_keys):
                cx = env_cxs[i] if i < len(env_cxs) else env_cxs[0]
                keys.append({"key": k, "cx": cx})
        
        # Priority 2: Backwards Compatibility (Individual suffixed keys & CSV)
        if not keys:
            # Try comma-separated legacy fallback
            legacy_keys = os.getenv("GOOGLE_SEARCH_KEYS") or ""
            legacy_cxs = os.getenv("GOOGLE_SEARCH_CXS") or os.getenv("GOOGLE_SEARCH_ENGINE_IDS") or ""
            
            keys_list = [k.strip() for k in legacy_keys.split(",") if k.strip()]
            cxs_list = [c.strip() for c in legacy_cxs.split(",") if c.strip()]
            
            if keys_list:
                default_cx = cxs_list[0] if cxs_list else os.getenv("GOOGLE_SEARCH_ENGINE_ID")
                for i, k in enumerate(keys_list):
                    cx = cxs_list[i] if i < len(cxs_list) else default_cx
                    if k and cx: keys.append({"key": k, "cx": cx})
            
            # Try individual keys
            if not keys:
                suffixes = [""] + [f"_{i}" for i in range(1, 11)]
                for s in suffixes:
                    k, cx = os.getenv(f"GOOGLE_SEARCH_API_KEY{s}"), os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{s}")
                    if k and cx: keys.append({"key": k, "cx": cx})

        if not keys:
            logger.warning("⚠️ [ContentOrchestrator] No Google Search Keys configured in .env!")

        self.discovery = DiscoveryHunter(keys)
        self.vision = vision or VisionInsight(discovery_hunter=self.discovery)
        # V76.6: Removed hardcoded `TIER3_MODEL`. Allow TrinityBridge to use Database Priority!
        self.pen = pen or CreativePen(model_name=None)
        self.cop = cop or PlagiarismCop()
        self.media = media or MediaCompressor()
        
        # AssetHunter config
        self.hunter = hunter or AssetHunter(keys)
            
        self.semaphore = asyncio.Semaphore(ORCHESTRATOR_SEMAPHORE_LIMIT)
        
        # Step Registry
        registry.register(1, self.vision); registry.register(2, self.hunter)
        registry.register(3, self.pen); registry.register(4, self.pen)
        registry.register(5, self.cop) # Fixed: Step 5 now automated via PlagiarismCop
        registry.register(6, self.media)
        
        # Initialize Handlers
        self.voice_handler = VoiceHandler(self)
        self.action_handler = ActionHandler(self)
        self.engine = ExecutionEngine(self)
        self.analyst = AnalystHandler(self)
        self.management = ManagementHandler(self)
        
        logger.info("[Content Factory] Orchestrator initialized with lean modular handlers.")

    async def resume_all(self):
        """R104: Self-Healing Resume logic. R1.5: Zero-Hydration — only select needed columns."""
        session_maker = alchemy_config.create_session_maker()
        async with session_maker() as session:
            stmt = select(ContentCampaign.id, ContentCampaign.current_step).where(
                ContentCampaign.status == "PROCESSING"
            )
            result = await session.execute(stmt)
            rows = result.all()
            for row in rows:
                asyncio.create_task(self.engine.trigger_step(row.id, force_step=row.current_step))

    # --- Delegated API Surface ---

    async def handle_voice_request(self, transcript: str, campaign_repo: ContentCampaignRepository, tenant_id: str = "default", user_id: Optional[str] = None, intent_data: Optional[Dict] = None) -> IntentResponse:
        return await self.voice_handler.handle_request(transcript, campaign_repo, tenant_id, user_id, intent_data=intent_data)

    async def get_active_campaign(self, campaign_repo: ContentCampaignRepository, user_id: Optional[str] = None, tenant_id: str = "default", query: Optional[str] = None) -> Optional[ContentCampaign]:
        return await self.voice_handler.get_active_campaign(campaign_repo, user_id, tenant_id, query=query)

    async def approve_step(self, campaign_id: str, data: Dict[str, Union[str, int, float, bool, Dict[str, object], List[object]]], campaign_repo: ContentCampaignRepository) -> GenericResponse:
        return await self.action_handler.approve_step(campaign_id, data, campaign_repo)

    async def retry_step(self, campaign_id: str, campaign_repo: ContentCampaignRepository) -> GenericResponse:
        return await self.action_handler.retry_step(campaign_id, campaign_repo)

    async def update_metadata(self, campaign_id: str, data: Dict[str, Union[str, int, float, bool, Dict[str, object], List[object]]], campaign_repo: ContentCampaignRepository) -> GenericResponse:
        return await self.action_handler.update_metadata(campaign_id, data, campaign_repo)

    async def _trigger_next_step(self, campaign_id: str, force_step: Optional[int] = None) -> None:
        await self.engine.trigger_step(campaign_id, force_step)

# Singleton
content_factory = ContentOrchestrator()
