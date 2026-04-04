import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.intent import IntentResponse, IntentAction, RouterTier
from .tier2_cloud import Tier2CloudRouter
from .tier3_cloud import Tier3CloudRouter
from .tier2_refiner import Tier2Refiner
from backend.services.ai_engine.core.semantic_router import SemanticRouter
from .intent_resolver import RouterResolver
from .intent_executor import RouterExecutor

logger = logging.getLogger("api-gateway")

class RouterOrchestrator:
    """
    C.O.R.E ARCHITECTURE — Central Orchestrated Routing Engine.
    Modularized for Martial Law (<300 lines).
    """
    def __init__(self):
        self.semantic_router = SemanticRouter()
        self.t2_router = Tier2CloudRouter()
        self.t3_router = Tier3CloudRouter()
        self.t2_refiner = Tier2Refiner()
        
        self.resolver = RouterResolver(self.semantic_router, self.t2_router)
        self.executor = RouterExecutor(self.t3_router, self.t2_refiner)

    async def classify(self, db: AsyncSession, transcript: str, user_id: str, app_state: dict, context=None, screen_context=None, modality="text") -> IntentResponse:
        """Phase 1: Intent Resolution (T1 -> T2 Dispatch)."""
        return await self.resolver.classify(db, transcript, user_id, app_state, context, screen_context, modality)

    async def execute(self, classification: IntentResponse, transcript: str, context: Optional[List[Dict[str, object]]] = None, screen_context: Optional[Dict[str, object]] = None, **kwargs) -> IntentResponse:
        """Phase 2: Action Execution (Phase 3 of Trinity Loop)."""
        return await self.executor.execute(classification, transcript, context, screen_context, **kwargs)

orchestrator = RouterOrchestrator()
