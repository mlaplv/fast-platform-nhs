import os
import time
import logging
import asyncio
from typing import List, Optional, Any, Callable
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from ai_engine.core.key_rotator import SmartKeyRotator

logger = logging.getLogger("ai-engine")

class TrinityModelBridge:
    """
    Centralized dispatcher for Gemini models with Waterfall fallback and key rotation.
    Decouples model availability from business logic.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TrinityModelBridge, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.rotator = SmartKeyRotator()
        # Health tracking: { "model:key": cooldown_until_timestamp }
        self._health_map = {} 
        # Predictive cache: Tuple(model_name, api_key)
        self._last_known_good = (None, None) 
        self._initialized = True

    async def run(
        self,
        agent: Agent,
        transcript: str,
        deps: Any = None,
        message_history: List[Any] = None,
        model_waterfall: Optional[List[str]] = None
    ) -> Any:
        """
        Runs an agent with Predictive Waterfall fallback.
        1. Tries Last Known Good (0ms overhead if successful).
        2. Tries Waterfall tiers, skipping keys/models marked as 'Cooling Down'.
        """
        import time
        now = time.time()

        if not model_waterfall:
            waterfall_str = os.getenv(
                "MODEL_WATERFALL", 
                "gemini-2.5-pro,gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash"
            )
            model_names = [m.strip() for m in waterfall_str.split(",")]
        else:
            model_names = model_waterfall

        all_keys = self.rotator.get_all_keys()

        # --- PHASE 1: PREDICTIVE HIT (Zero Latency) ---
        lk_model, lk_key = self._last_known_good
        if lk_model and lk_key:
            # Check if still healthy
            if self._health_map.get(f"{lk_model}:{lk_key}", 0) < now:
                try:
                    os.environ.pop("GOOGLE_API_KEY", None)
                    provider = GoogleProvider(api_key=lk_key)
                    model_instance = GoogleModel(lk_model, provider=provider)
                    result = await agent.run(transcript, deps=deps, message_history=message_history, model=model_instance)
                    logger.debug(f"[TrinityBridge] Predictive HIT: {lk_model}")
                    return result
                except Exception:
                    # Silent fail, drop into standard waterfall
                    logger.debug(f"[TrinityBridge] Predictive MISS: {lk_model}")
                    self._health_map[f"{lk_model}:{lk_key}"] = now + 60 # Cooldown 1m

        # --- PHASE 2: INTELLIGENT WATERFALL ---
        for model_name in model_names:
            # Try all available keys for this tier, skipping unhealthy ones
            for _ in range(len(all_keys)):
                api_key = self.rotator.get_next_key()
                
                # Intelligent Skip: If key is cooling down, skip instantly
                if self._health_map.get(f"{model_name}:{api_key}", 0) > now:
                    continue

                os.environ.pop("GOOGLE_API_KEY", None)
                
                try:
                    provider = GoogleProvider(api_key=api_key)
                    model_instance = GoogleModel(model_name, provider=provider)
                    
                    result = await agent.run(
                        transcript,
                        deps=deps,
                        message_history=message_history,
                        model=model_instance
                    )
                    
                    # Success: Mark as healthy and Last Known Good
                    self._last_known_good = (model_name, api_key)
                    self._health_map.pop(f"{model_name}:{api_key}", None)
                    
                    logger.info(f"[TrinityBridge] Success: {model_name} (key {api_key[:8]}...)")
                    return result

                except Exception as e:
                    err_str = str(e).upper()
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        logger.warning(f"[TrinityBridge] {model_name} key {api_key[:8]}... BUSY (429). Marking Cooldown.")
                        self._health_map[f"{model_name}:{api_key}"] = now + 60 # 1 minute block
                    elif "400" in err_str or "INVALID" in err_str:
                        logger.error(f"[TrinityBridge] {model_name} INVALID KEY. Marking Dead.")
                        self._health_map[f"{model_name}:{api_key}"] = now + 3600 # 1 hour block
                    else:
                        logger.error(f"[TrinityBridge] {model_name} Error: {e}")
                    
                    continue

    def _update_health(self, model: str, key: str, healthy: bool):
        """Update the health status of a model/key pair."""
        now = time.time() if not healthy else 0
        self._health_map[f"{model}:{key}"] = now + (60 if not healthy else 0)

    async def run_stream(
        self,
        agent: Agent,
        transcript: str,
        deps: Any = None,
        message_history: List[Any] = None,
        model_waterfall: Optional[List[str]] = None
    ) -> Any:
        """
        Streaming version of run() with full Waterfall fallback and Key Rotation.
        """
        import time
        now = time.time()

        if not model_waterfall:
            waterfall_str = os.getenv(
                "MODEL_WATERFALL", 
                "gemini-2.0-flash,gemini-1.5-flash"
            )
            model_names = [m.strip() for m in waterfall_str.split(",")]
        else:
            model_names = model_waterfall

        all_keys = self.rotator.get_all_keys()

        # Try Tiered Waterfall
        for model_name in model_names:
            for _ in range(len(all_keys)):
                api_key = self.rotator.get_next_key()
                
                # Health Check
                if self._health_map.get(f"{model_name}:{api_key}", 0) > now:
                    continue

                try:
                    provider = GoogleProvider(api_key=api_key)
                    model_instance = GoogleModel(model_name, provider=provider)
                    
                    # We return the stream immediately. 
                    # Note: Errors during streaming connection will be caught by the caller's 'async with'
                    # But the initial model instantiation and agent.run_stream call should be safe here.
                    logger.debug(f"[TrinityBridge] Attempting Stream: {model_name} (key {api_key[:8]}...)")
                    
                    # Store as potential LKG if successful (though we don't know yet)
                    self._last_known_good = (model_name, api_key)
                    
                    return agent.run_stream(
                        transcript,
                        deps=deps,
                        message_history=message_history,
                        model=model_instance
                    )

                except Exception as e:
                    logger.warning(f"[TrinityBridge] Stream Init Fail {model_name}: {e}")
                    continue

        # Last Resort: Try one more time with a fresh key from the pool
        api_key = self.rotator.get_next_key()
        model_name = model_names[-1]
        provider = GoogleProvider(api_key=api_key)
        model_instance = GoogleModel(model_name, provider=provider)
        return agent.run_stream(transcript, deps=deps, message_history=message_history, model=model_instance)

# Singleton instance
trinity_bridge = TrinityModelBridge()
