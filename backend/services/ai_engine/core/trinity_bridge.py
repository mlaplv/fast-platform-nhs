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
        self.success_model_key = "ai:bridge:last_success_model"

    async def run(self, agent: Agent, prompt: str, **kwargs):
        """
        Runs an AI Agent with managed context and dynamic model/key injection.
        V63.0: Sticky success, smart error classification, and multi-level fallback.
        """
        # 1. Determine priority model chain
        requested_model = kwargs.pop("model", None)
        
        # Priority order: 
        # a) Explicitly requested model
        # b) Last successful model (Sticky)
        # c) Default TIER2 model
        # d) Fallback TIER2 model
        
        models_to_try = []
        if requested_model:
            models_to_try.append(requested_model)
            
        sticky_model = None
        if self.rotator._use_redis:
            try:
                sticky_model = await self.rotator.client.get(self.success_model_key)
            except Exception: pass
            
        if sticky_model and sticky_model not in models_to_try:
            models_to_try.append(sticky_model)
            
        if self.default_model_name not in models_to_try:
            models_to_try.append(self.default_model_name)
            
        if self.fallback_model_name and self.fallback_model_name not in models_to_try:
            models_to_try.append(self.fallback_model_name)
            
        max_keys = max(1, self.rotator.get_count())
        import asyncio
        
        last_error = None

        for model_name in models_to_try:
            # For each model, try all keys if needed, starting from the sticky best key
            for attempt in range(max_keys):
                key = await self.rotator.get_key()
                # R101/R106: Set the API key in environment for the current execution
                os.environ["GOOGLE_API_KEY"] = key
                os.environ["GEMINI_API_KEY"] = key 
                model = GeminiModel(model_name)
                
                try:
                    logger.info(f"[TrinityBridge] {model_name} (Attempt {attempt+1}/{max_keys})...")
                    res = await agent.run(prompt, model=model, **kwargs)
                    
                    # Store SUCCESS state (Sticky)
                    await self.rotator.set_success(key)
                    if self.rotator._use_redis:
                        await self.rotator.client.set(self.success_model_key, model_name)
                    
                    return res
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    
                    # ─── CATEGORY A: NON-ROTATABLE ERRORS (FAIL FAST) ───
                    # If the prompt is too long, content blocked by safety, or logic error, rotating keys won't help.
                    if any(p in error_str for p in ["context_length_exceeded", "too many tokens", "safety", "blocked", "invalid_argument", "400"]):
                        # Exception: "400 API key not valid" IS rotatable, so we check for it specifically
                        if "api key not valid" in error_str or "invalid_key" in error_str:
                            pass # Fall through to Category B
                        else:
                            logger.error(f"[TrinityBridge] Non-rotatable error for {model_name}: {e}")
                            raise AIConfigurationError(f"AI Fail-Fast: {str(e)}", model_name, attempt)

                    # ─── CATEGORY B: ROTATABLE ERRORS (TRY NEXT KEY) ───
                    # R109: If this model doesn't support tools, rotating keys is useless. Switch model immediately.
                    if "tool output is not supported" in error_str:
                        logger.warning(f"[TrinityBridge] Model {model_name} DOES NOT support Tool calling. Jumping to next model...")
                        break 
                    
                    if any(p in error_str for p in ["429", "quota", "rate limit", "timeout"]):
                        logger.warning(f"[TrinityBridge] 429/Timeout for {model_name}. Key index marked COOLDOWN.")
                        await self.rotator.mark_unhealthy(key)
                        await asyncio.sleep(0.5)
                        continue
                        
                    if any(p in error_str for p in ["503", "unavailable", "500", "auth", "401", "403", "api key not valid", "invalid"]):
                        logger.warning(f"[TrinityBridge] Auth/Server Error for {model_name}. Rotating key...")
                        await self.rotator.mark_unhealthy(key)
                        continue
                        
                    if "model not found" in error_str or "404" in error_str:
                        logger.warning(f"[TrinityBridge] Model {model_name} not found. Jumping to next model...")
                        break 
                        
                    # Default: Unknown error, try next key just in case
                    logger.error(f"[TrinityBridge] Unknown AI Error for {model_name}: {e}")
                    continue
                        
        logger.error(f"[TrinityBridge] Exhausted all keys and fallback models!")
        raise AIConfigurationError(
            f"Tất cả Model/Key đã cạn kiệt. Lỗi cuối: {str(last_error)}",
            models_to_try[-1] if models_to_try else "N/A",
            max_keys - 1
        )

trinity_bridge = TrinityBridge()
