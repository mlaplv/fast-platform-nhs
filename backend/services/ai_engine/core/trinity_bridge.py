import logging
import os
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from backend.services.ai_engine.core.key_rotator import SmartKeyRotator

logger = logging.getLogger("api-gateway")

class AIConfigurationError(Exception):
    """Detailed error for AI diagnostics (V62.2)"""
    def __init__(self, message: str, model: str = None, key_index: int = None):
        super().__init__(message)
        self.model = model
        self.key_index = (key_index + 1) if key_index is not None else None

class TrinityBridge:
    """
    V61.0: Centralized AI Bridge for Managed Calls.
    Handles Key Rotation, Token Budgeting, and Circuit Breaking.
    """
    def __init__(self):
        self.rotator = SmartKeyRotator()
        self.default_model_name = os.getenv("TIER2_MODEL", "gemini-2.5-flash")
        self.fallback_model_name = os.getenv("TIER2_FALLBACK_MODEL", "gemini-2.5-pro")

    async def run(self, agent: Agent, prompt: str, **kwargs):
        """
        Runs an AI Agent with managed context and dynamic model/key injection.
        R101/R106: Centralized entry point. Applies Rule 2.7 (Fallback Chain + Backoff).
        """
        # Attempt primary model, then fallback model
        models_to_try = [kwargs.pop("model", self.default_model_name)]
        if self.fallback_model_name and self.fallback_model_name not in models_to_try:
            models_to_try.append(self.fallback_model_name)
            
        max_keys = max(1, self.rotator.get_count())
        
        import asyncio
        
        for model_name in models_to_try:
            for attempt in range(max_keys):
                key = self.rotator.get_key()
                # R101/R106: Set the API key in environment for the current execution
                os.environ["GOOGLE_API_KEY"] = key
                os.environ["GEMINI_API_KEY"] = key 
                model = GeminiModel(model_name)
                
                try:
                    logger.info(f"[TrinityBridge] Executing {model_name} (Attempt {attempt+1}/{max_keys})...")
                    return await agent.run(prompt, model=model, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    if "tool output is not supported" in error_str:
                        # R109: If this model doesn't support tools, rotating keys is useless. Switch model immediately.
                        logger.warning(f"[TrinityBridge] Model {model_name} DOES NOT support Tool calling. Jumping to next model...")
                        break 
                    
                    if "429" in error_str or "quota" in error_str or "rate limit" in error_str or "timeout" in error_str:
                        # R2.7 Fail-Fast on exhaustion: 
                        # Only wait 0.5s before rotating to the next key. If all keys fail, we fallback to TIER2_FALLBACK_MODEL.
                        wait_time = 0.5
                        logger.warning(f"[TrinityBridge] 429/Timeout for {model_name}. Backoff {wait_time}s. Error: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    elif "503" in error_str or "service unavailable" in error_str or "500" in error_str:
                        logger.warning(f"[TrinityBridge] 50X Error for {model_name}. Rotating key... Error: {e}")
                        continue
                    elif "auth" in error_str or "401" in error_str or "403" in error_str:
                        logger.error(f"[TrinityBridge] Auth Error for {model_name}. Rotating key... Error: {e}")
                        continue
                    else:
                        logger.error(f"[TrinityBridge] Unhandled AI Error for {model_name}: {e}")
                        raise AIConfigurationError(f"Unhandled AI Error: {str(e)}", model_name, attempt)
                        
        logger.error(f"[TrinityBridge] Exhausted all keys and fallback models!")
        # Thống kê lỗi cuối cùng để báo cáo sếp
        raise AIConfigurationError(
            f"Tất cả Model/Key đã cạn kiệt. Lần thử cuối: {models_to_try[-1]} (Key index: {max_keys})",
            models_to_try[-1],
            max_keys - 1
        )

trinity_bridge = TrinityBridge()
