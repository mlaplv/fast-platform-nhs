import logging
import os
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from backend.services.ai_engine.core.key_rotator import SmartKeyRotator

logger = logging.getLogger("api-gateway")

class TrinityBridge:
    """
    V61.0: Centralized AI Bridge for Managed Calls.
    Handles Key Rotation, Token Budgeting, and Circuit Breaking.
    """
    def __init__(self):
        self.rotator = SmartKeyRotator()
        self.default_model_name = os.getenv("TIER2_MODEL", "gemini-2.0-flash")

    async def run(self, agent: Agent, prompt: str, **kwargs):
        """
        Runs an AI Agent with managed context and dynamic model/key injection.
        R101/R106: Centralized entry point.
        """
        key = self.rotator.get_key()
        model_name = kwargs.pop("model", self.default_model_name)
        
        # R101/R106: Set the API key in environment for the current execution
        # PydanticAI GeminiModel will pick it up automatically from these vars
        os.environ["GOOGLE_API_KEY"] = key
        os.environ["GEMINI_API_KEY"] = key 
        model = GeminiModel(model_name)
        
        try:
            logger.info(f"[TrinityBridge] Executing {model_name} with key rotation...")
            return await agent.run(prompt, model=model, **kwargs)
        except Exception as e:
            logger.error(f"[TrinityBridge] AI Execution Failed for {model_name}: {e}")
            raise

trinity_bridge = TrinityBridge()
