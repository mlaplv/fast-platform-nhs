import os
import logging
import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Union, List, Protocol, runtime_checkable

from backend.services.campaign_service import campaign_service
from backend.services.creative_studio.vision_insight import VisionInsight
from backend.services.creative_studio.asset_hunter import AssetHunter
from backend.services.creative_studio.creative_pen import CreativePen
from backend.services.creative_studio.plagiarism_cop import PlagiarismCop
from backend.services.creative_studio.media_compressor import MediaCompressor
from backend.constants.agentic import ORCHESTRATOR_SEMAPHORE_LIMIT
from backend.database.alchemy_config import alchemy_config
from backend.schemas.intent import IntentResponse
from backend.schemas.campaign import GenericResponse, AgentResponse

# Modular Handlers
from backend.services.creative_studio.voice import VoiceHandler
from backend.services.creative_studio.actions import ActionHandler
from backend.services.creative_studio.engine import ExecutionEngine

logger = logging.getLogger("api-gateway")

@runtime_checkable
class Operative(Protocol):
    """R107: Protocol for Content Factory Operatives."""
    async def execute(self, campaign_id: str, session: AsyncSession, **kwargs: object) -> "AgentResponse":
        ...

class OperativeRegistry:
    """
    V61.0: Lightweight DI Registry using Borg Pattern.
    Saves RAM by avoiding heavy DI frameworks while allowing dynamic agent swapping.
    """
    _shared_state: Dict[str, object] = {}

    def __init__(self):
        self.__dict__ = self._shared_state
        if not hasattr(self, 'operatives'):
            self.operatives: Dict[int, Operative] = {}

    def register(self, step: int, operative: Operative):
        """Register an operative for a specific workflow step."""
        self.operatives[step] = operative
        logger.info(f"[Registry] Operative registered for Step {step}: {type(operative).__name__}")

    def get_operative(self, step: int) -> Operative:
        """Retrieve the operative for a specific step."""
        operative = self.operatives.get(step)
        if not operative:
            raise ValueError(f"No operative registered for Step {step}")
        return operative

# Global singleton
registry = OperativeRegistry()

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
        registry.register(5, self.cop) # Fixed: Step 5 now automated via PlagiarismCop
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
            sql = text("SELECT id, current_step FROM content_campaigns WHERE status = 'PROCESSING' AND deleted_at IS NULL")
            result = await session.execute(sql)
            rows = result.all()
            for row in rows:
                asyncio.create_task(self.engine.trigger_step(str(row[0]), force_step=int(row[1])))

    # --- Delegated API Surface ---

    async def handle_voice_request(self, transcript: str, session: AsyncSession, tenant_id: str = "default", user_id: Optional[str] = None, intent_data: Optional[Dict[str, object]] = None) -> IntentResponse:
        return await self.voice_handler.handle_request(transcript, session, tenant_id, user_id, intent_data=intent_data)

    async def get_active_campaign(self, session: AsyncSession, user_id: Optional[str] = None, tenant_id: str = "default", query: Optional[str] = None) -> Optional[Dict[str, object]]:
        return await self.voice_handler.get_active_campaign(session, user_id, tenant_id, query=query)

    async def approve_step(self, campaign_id: str, data: Dict[str, object], session: AsyncSession) -> GenericResponse:
        return await self.action_handler.approve_step(campaign_id, data, session)

    async def retry_step(self, campaign_id: str, session: AsyncSession) -> GenericResponse:
        return await self.action_handler.retry_step(campaign_id, session)

    async def update_metadata(self, campaign_id: str, data: Dict[str, object], session: AsyncSession) -> GenericResponse:
        return await self.action_handler.update_metadata(campaign_id, data, session)

    async def _trigger_next_step(self, campaign_id: str, force_step: int = None):
        await self.engine.trigger_step(campaign_id, force_step)

# Singleton
content_factory = ContentOrchestrator()
