import logging
import os
from contextlib import asynccontextmanager
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from backend.services.ai_engine.core.key_rotator import key_rotator

logger = logging.getLogger("api-gateway")

class AIConfigurationError(Exception):
    """Detailed error for AI diagnostics (V62.2)"""
    def __init__(self, message: str, model: str = None, key_index: int = None):
        super().__init__(message)
        self.model = model
        self.key_index = (key_index + 1) if key_index is not None else None

class TrinityBridge:
    """
    V65.0: Centralized AI Bridge for Managed Calls.
    Handles Key Rotation, Token Budgeting, and Circuit Breaking.
    Fixed: No more os.environ race condition — API key passed directly via GoogleProvider.
    """
    def __init__(self):
        self.rotator = key_rotator
        # V71.17: Neural Waterfall Support (2026 Edition)
        self.default_model_name = os.getenv("TIER2_MODEL", "gemini-2.5-flash")
        self.fallback_model_name = os.getenv("TIER2_FALLBACK_MODEL", "gemini-2.0-flash")

        # Load full waterfall if provided
        waterfall = os.getenv("MODEL_WATERFALL", "")
        self.model_waterfall = [m.strip() for m in waterfall.split(",") if m.strip()] if waterfall else []

        self.success_model_key = "ai:bridge:last_success_model"

    def _build_model_chain(self) -> list[str]:
        """Build priority model chain (shared between run and run_stream)."""
        models = []
        if self.model_waterfall:
            for m in self.model_waterfall:
                if m not in models:
                    models.append(m)
        if self.default_model_name not in models:
            models.append(self.default_model_name)
        if self.fallback_model_name and self.fallback_model_name not in models:
            models.append(self.fallback_model_name)
        return models

    async def _get_sticky_model(self) -> str | None:
        """Get last successful model from Redis."""
        if not self.rotator._use_redis:
            return None
        try:
            val = await self.rotator.client.get(self.success_model_key)
            return val if val else None
        except Exception:
            return None

    async def _save_sticky_model(self, model_name: str):
        """Save last successful model to Redis."""
        if self.rotator._use_redis:
            try:
                await self.rotator.client.set(self.success_model_key, model_name)
            except Exception:
                pass

    def _create_model(self, model_name: str, api_key: str) -> GoogleModel:
        """Create a GoogleModel with the API key passed directly (no env race)."""
        provider = GoogleProvider(api_key=api_key)
        return GoogleModel(model_name, provider=provider)

    def _classify_error(self, error_str: str) -> str:
        """Classify error for routing decisions. Returns: 'fail_fast', 'rate_limit', 'auth', 'model_not_found', 'tool_unsupported', 'unknown'."""
        # Non-rotatable (fail fast) — except "api key not valid" which IS rotatable
        if any(p in error_str for p in ["context_length_exceeded", "too many tokens", "safety", "blocked", "invalid_argument", "400"]):
            if "api key not valid" in error_str or "invalid_key" in error_str:
                return "auth"
            return "fail_fast"

        if "tool output is not supported" in error_str:
            return "tool_unsupported"

        if any(p in error_str for p in ["429", "quota", "rate limit", "limit reached"]):
            return "rate_limit"

        if any(p in error_str for p in ["503", "unavailable", "500", "auth", "401", "403", "api key not valid", "invalid"]):
            return "auth"

        if "model not found" in error_str or "404" in error_str:
            return "model_not_found"

        return "unknown"

    async def run(self, agent: Agent, prompt: str, **kwargs):
        """
        Runs an AI Agent with managed context and dynamic model/key injection.
        V65.0: API key passed directly via GoogleProvider — no env race condition.
        """
        requested_model = kwargs.pop("model", None)
        session_id = kwargs.pop("session_id", None)

        models_to_try = []
        if requested_model:
            models_to_try.append(requested_model)

        base_chain = self._build_model_chain()
        sticky_model = await self._get_sticky_model()

        if sticky_model and sticky_model not in models_to_try:
            models_to_try.append(sticky_model)
        for m in base_chain:
            if m not in models_to_try:
                models_to_try.append(m)

        max_keys = max(1, self.rotator.get_count())
        import asyncio

        last_error = None

        for model_name in models_to_try:
            for attempt in range(max_keys):
                key = await self.rotator.get_key(session_id=session_id)
                model = self._create_model(model_name, api_key=key)

                try:
                    logger.info(f"[TrinityBridge] {model_name} (Attempt {attempt+1}/{max_keys}) (Session: {session_id})...")
                    res = await agent.run(prompt, model=model, **kwargs)

                    await self.rotator.set_success(key, session_id=session_id)
                    await self._save_sticky_model(model_name)
                    return res

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    category = self._classify_error(error_str)

                    if category == "fail_fast":
                        logger.error(f"[TrinityBridge] Non-rotatable error for {model_name}: {e}")
                        raise AIConfigurationError(f"AI Fail-Fast: {str(e)}", model_name, attempt)

                    if category == "tool_unsupported":
                        logger.warning(f"[TrinityBridge] Model {model_name} DOES NOT support Tool calling. Jumping to next model...")
                        break

                    if category == "rate_limit":
                        reason = "daily" if "daily" in error_str or "quota" in error_str else "rate_limit"
                        logger.warning(f"[TrinityBridge] {reason.upper()} for {model_name}. Key marked UNHEALTHY.")
                        await self.rotator.mark_unhealthy(key, reason=reason, session_id=session_id)
                        await asyncio.sleep(0.5)
                        continue

                    if category == "auth":
                        logger.warning(f"[TrinityBridge] Auth/Server Error for {model_name}. Rotating key...")
                        await self.rotator.mark_unhealthy(key, reason="auth_or_server", session_id=session_id)
                        continue

                    if category == "model_not_found":
                        logger.warning(f"[TrinityBridge] Model {model_name} not found. Jumping to next model...")
                        break

                    # Unknown error
                    logger.error(f"[TrinityBridge] Unknown AI Error for {model_name}: {e}")
                    continue

        logger.error(f"[TrinityBridge] Exhausted all keys and fallback models!")
        raise AIConfigurationError(
            f"Hệ thống AI đang tạm thời quá tải (Limit reached). Sếp vui lòng đợi 5-10 phút hoặc nâng cấp API Key nhé! Lỗi kỹ thuật: {str(last_error)}",
            models_to_try[-1] if models_to_try else "N/A",
            max_keys - 1
        )

    @asynccontextmanager
    async def run_stream(self, agent: Agent, prompt: str, **kwargs):
        """
        Streaming version of run().
        V65.0: API key passed directly via GoogleProvider — no env race condition.
        """
        requested_model = kwargs.pop("model", None)
        session_id = kwargs.pop("session_id", None)

        models_to_try = []
        if requested_model:
            models_to_try.append(requested_model)

        base_chain = self._build_model_chain()
        sticky_model = await self._get_sticky_model()

        if sticky_model and sticky_model not in models_to_try:
            models_to_try.append(sticky_model)
        for m in base_chain:
            if m not in models_to_try:
                models_to_try.append(m)

        max_keys = max(1, self.rotator.get_count())
        import asyncio
        last_error = None

        for model_name in models_to_try:
            for attempt in range(max_keys):
                key = await self.rotator.get_key(session_id=session_id)
                model = self._create_model(model_name, api_key=key)

                try:
                    logger.info(f"[TrinityBridge][Stream] {model_name} (Attempt {attempt+1}/{max_keys}) (Session: {session_id})...")
                    async with agent.run_stream(prompt, model=model, **kwargs) as stream:
                        yield stream

                    await self.rotator.set_success(key, session_id=session_id)
                    await self._save_sticky_model(model_name)
                    return

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    category = self._classify_error(error_str)

                    if category == "fail_fast":
                        logger.error(f"[TrinityBridge][Stream] Non-rotatable error for {model_name}: {e}")
                        raise AIConfigurationError(f"AI Fail-Fast: {str(e)}", model_name, attempt)

                    if category == "rate_limit":
                        reason = "daily" if "daily" in error_str or "quota" in error_str else "rate_limit"
                        logger.warning(f"[TrinityBridge][Stream] {reason.upper()} for {model_name}. Key marked UNHEALTHY.")
                        await self.rotator.mark_unhealthy(key, reason=reason, session_id=session_id)
                        await asyncio.sleep(0.5)
                        continue

                    if category == "auth":
                        logger.warning(f"[TrinityBridge][Stream] Auth/Server Error for {model_name}. Rotating key...")
                        await self.rotator.mark_unhealthy(key, reason="auth_or_server", session_id=session_id)
                        continue

                    if category == "model_not_found":
                        logger.warning(f"[TrinityBridge][Stream] Model {model_name} not found. Jumping to next model...")
                        break

                    logger.error(f"[TrinityBridge][Stream] Unknown AI Error: {e}")
                    continue

        raise AIConfigurationError(f"Hệ thống AI đang tạm thời quá tải cho Stream. Sếp vui lòng đợi 5-10 phút nhé! Lỗi kỹ thuật: {str(last_error)}")

trinity_bridge = TrinityBridge()
