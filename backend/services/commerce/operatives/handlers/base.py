"""
Base Classes for Decentralized Specialist Architecture (Elite V2.5)
=================================================================
Defines the Context Bus and Handler interfaces for modular AI Support.
"""
from __future__ import annotations
from typing import Optional, List, Dict, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field, JsonValue
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.support import SupportRequest, SupportIntent, SupportProductInfo

from backend.services.commerce.logic.lead_extractor import ExtractedLead

class NeuralDNA(BaseModel):
    """Elite V2.2: Customer Personality & Segment DNA."""
    model_config = ConfigDict(strict=True)
    segment: str = Field(default="NEW", description="VIP | NEW | CHURN")
    vibe: str = Field(default="PROFESSIONAL", description="WARM | PROFESSIONAL")
    purchase_count: int = 0
    total_spent: float = 0.0
    last_hook: Optional[str] = None

class SupportContext(BaseModel):
    """Elite V2.5: The shared context bus for Helen AI Handlers."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    db: AsyncSession
    request: SupportRequest
    session_id: str
    
    # State data
    dna: NeuralDNA = Field(default_factory=NeuralDNA)
    product_ctx: str = ""
    history_text: str = ""
    knowledge_index: str = "" # Elite V2.2: Layer 1 Memory (Knowledge Map)
    p_info: Optional[SupportProductInfo] = None
    
    # Lead / Order results
    lead_data: Optional[ExtractedLead] = None
    processed_order_id: Optional[str] = None
    
    # Composed response
    replies: List[str] = Field(default_factory=list)
    intent: SupportIntent = SupportIntent.UNKNOWN
    ui_component: Optional[str] = None
    ui_metadata: Optional[Dict[str, JsonValue]] = None
    
    # Integration Status (Elite V2.2)
    zalo_enabled: bool = True
    messenger_enabled: bool = True
    
    # FOMO Metrics (Elite V2.2 - Social Proof & Scarcity)
    active_visitors: int = 1
    product_stock: Optional[int] = 0

# Late binding for Pydantic V2
SupportContext.model_rebuild()

class BaseHandler:
    """Interface for Helen specialist handlers."""
    async def handle(self, ctx: SupportContext) -> bool:
        """
        Execute handler logic.
        Return True if this handler 'consumed' the intent or wants to stop the pipeline.
        Return False to continue to next handler.
        """
        raise NotImplementedError
