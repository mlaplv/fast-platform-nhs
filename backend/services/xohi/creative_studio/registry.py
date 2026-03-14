import logging
from typing import Dict, Union, Type, Protocol, runtime_checkable, Awaitable, Callable, Optional
from backend.database.repositories import ContentCampaignRepository

logger = logging.getLogger("xohi.registry")

@runtime_checkable
class Operative(Protocol):
    """R107: Protocol for Content Factory Operatives."""
    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> "AgentResponse":
        ...

class OperativeRegistry:
    from backend.services.xohi.creative_studio.models.schemas import AgentResponse # Type checking
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
