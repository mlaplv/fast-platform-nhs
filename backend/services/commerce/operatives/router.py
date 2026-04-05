import logging
from typing import List
from backend.services.commerce.operatives.handlers.base import SupportContext, BaseHandler
from backend.services.commerce.operatives.handlers.guardrail import GuardrailHandler
from backend.services.commerce.operatives.handlers.order import OrderHandler
from backend.services.commerce.operatives.handlers.consultant import ConsultantHandler
from backend.services.commerce.operatives.handlers.greeting import GreetingHandler

logger = logging.getLogger("api-gateway")

class SupportRouter:
    """
    The Specialized Orchestrator (Elite V2.5 Architecture).
    Coordinates specialists to handle 5 Zones of Interaction.
    """
    
    def __init__(self):
        # The Strategic Pipeline Sequence (Elite V2.2: Action-First Optimization)
        self.handlers: List[BaseHandler] = [
            GuardrailHandler(),  # Priority 1: Safety/Rejection (Can terminate)
            OrderHandler(),      # Priority 2: Order Closing (Action-First, Can terminate)
            GreetingHandler(),   # Priority 3: Persona Greeting (Pass-through/Early Exit)
            ConsultantHandler()  # Priority 4: Knowledge Advice (Final recourse)
        ]
        
    async def process(self, ctx: SupportContext) -> SupportContext:
        """Execute the pipeline of specialists based on priority hierarchy."""
        for handler in self.handlers:
            try:
                # If a handler returns True, it has 'consumed' the logic and stops further specialists.
                if await handler.handle(ctx):
                    logger.debug(f"[SupportRouter] Pipeline consumed by {handler.__class__.__name__}")
                    break
            except Exception as e:
                logger.error(f"[SupportRouter] Critical error in {handler.__class__.__name__}: {e}")
                continue # Try the next handler if one fails
                
        # Final Post-Processing logic can go here (formatting, etc.)
        return ctx
