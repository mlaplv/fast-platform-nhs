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
    def __init__(self, message: str, model: Optional[str] = None, key_index: Optional[int] = None):
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
        self.default_model_name = os.getenv("TIER2_MODEL", "gemini-2.0-flash")
        self.fallback_model_name = os.getenv("TIER2_FALLBACK_MODEL", "gemini-2.0-flash")

        # Dynamic Model Pool (V75)
        self.db_primary_model = None
        self.db_waterfall = []

        # Load full waterfall if provided
        waterfall = os.getenv("MODEL_WATERFALL", "")
        self.model_waterfall = [m.strip() for m in waterfall.split(",") if m.strip()] if waterfall else []

        self.success_model_key = "ai:bridge:last_success_model"
        
        # Initial load (Safe to fail if DB not ready)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.reload_models())
        except Exception:
            pass

    async def reload_models(self):
        """Standardized Model Loading: Fetches waterfall from DB (V75)."""
        from backend.database.alchemy_config import alchemy_config
        from backend.database.models import VoiceProfile
        from sqlalchemy import select

        session_maker = alchemy_config.create_session_maker()
        try:
            async with session_maker() as session:
                # We take the first profile's config (Shared settings)
                stmt = select(VoiceProfile).limit(1)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if profile:
                    self.db_primary_model = profile.primary_model
                    self.db_waterfall = profile.ai_models or []
                    logger.info(f"[TrinityBridge] Models hot-reloaded. Primary: {self.db_primary_model}, Chain: {len(self.db_waterfall)}")
        except Exception as e:
            logger.warning(f"[TrinityBridge] Could not hot-reload models from DB: {e}")


    def _build_model_chain(self) -> list[str]:
        """Build priority model chain (shared between run and run_stream)."""
        models = []
        
        # 1. DB Priority (V75)
        if self.db_primary_model:
            models.append(self.db_primary_model)
        if self.db_waterfall:
            for m in self.db_waterfall:
                if m not in models:
                    models.append(m)

        # 2. Waterfall ENV Priority
        if self.model_waterfall:
            for m in self.model_waterfall:
                if m not in models:
                    models.append(m)
        
        # 3. Default ENV Fallbacks
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
        """
        Classify error for routing decisions.
        Returns: 'fail_fast', 'rate_limit', 'auth', 'model_not_found', 'tool_unsupported', 'unknown'.
        """
        # R106: Strict Classification.
        if any(p in error_str for p in ["401", "403", "api key not valid", "invalid_key", "key_expired", "project disabled", "deleted"]):
            return "auth"

        # 400 errors (INVALID_ARGUMENT) → fail fast (bad prompt/config, not key issue)
        if any(p in error_str for p in ["context_length_exceeded", "too many tokens", "safety", "blocked", "invalid_argument", "400"]):
            return "fail_fast"

        if "tool output is not supported" in error_str:
            return "tool_unsupported"

        # resource_exhausted = Google gRPC code for quota exceeded (429 OR daily)
        if any(p in error_str for p in ["429", "quota", "rate limit", "limit reached", "resource_exhausted"]):
            return "rate_limit"

        # R106-FIX: Server errors (500, 503) are transient, not auth failures.
        if any(p in error_str for p in ["503", "unavailable", "500", "internal server error", "service unavailable"]):
            return "rate_limit"

        if "model not found" in error_str or "404" in error_str:
            return "model_not_found"

        return "unknown"

    def _is_daily_quota(self, error_str: str) -> bool:
        """Detect if a rate_limit error is actually a daily quota (not a per-minute spike)."""
        return any(p in error_str for p in ["daily", "per_day", "per day", "perday", "requests_per_day", "generaterequestsperdayperproject"])

    async def run(self, agent: Agent, prompt: str, **kwargs: object):
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
            daily_exhausted_count = 0  # Track how many keys hit daily quota for this model
            for attempt in range(max_keys):
                key = await self.rotator.get_key(session_id=session_id)

                # V73.0: Skip (key+model) combos already known to be daily-exhausted
                if await self.rotator.is_model_daily_exhausted(key, model_name):
                    daily_exhausted_count += 1
                    if daily_exhausted_count >= max_keys:
                        logger.warning(f"[TrinityBridge] ALL keys daily-exhausted for model '{model_name}'. Falling back to next model.")
                        break
                    continue

                model = self._create_model(model_name, api_key=key)

                try:
                    logger.info(f"[TrinityBridge] {model_name} (Attempt {attempt+1}/{max_keys}) (Session: {session_id})...")
                    res = await agent.run(prompt, model=model, **kwargs)

                    # V70.0: Track tokens on success
                    try:
                        usage = getattr(res, 'usage', None)
                        if usage:
                            total_tokens = getattr(usage, 'total_tokens', 0)
                            await self.rotator.track_tokens(key, total_tokens)
                    except Exception as te:
                        logger.debug(f"[TrinityBridge] Token tracking failed: {te}")

                    await self.rotator.set_success(key, session_id=session_id)
                    await self._save_sticky_model(model_name)
                    return res

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    category = self._classify_error(error_str)
                    
                    kid = self.rotator._get_key_id(key)
                    logger.warning(f"[TrinityBridge] Model: {model_name} | Key: {key[:8]}... | KID: {kid} | Category: {category} | Details: {error_str}")
                    
                    if "429 too many requests: hệ thống ai đang tạm thời đạt giới hạn an toàn" in error_str:
                        logger.error(f"[TrinityBridge] AI Engine overloaded, failing fast.")
                        raise AIConfigurationError(f"Hệ thống AI đang tạm thời vượt mức tải an toàn. Vui lòng thử lại sau 1 phút.", model_name, attempt)

                    if category == "fail_fast":
                        logger.error(f"[TrinityBridge] Non-rotatable error for {model_name}: {e}")
                        raise AIConfigurationError(f"AI Fail-Fast: {str(e)}", model_name, attempt)

                    if category == "tool_unsupported":
                        logger.warning(f"[TrinityBridge] Model {model_name} DOES NOT support Tool calling. Jumping to next model...")
                        break

                    if category == "rate_limit":
                        if self._is_daily_quota(error_str):
                            # V73.0: Lock only this (key, model) pair for 24h. Key stays alive for other models!
                            await self.rotator.mark_model_daily(key, model_name)
                            daily_exhausted_count += 1
                            if daily_exhausted_count >= max_keys:
                                logger.warning(f"[TrinityBridge] ALL keys daily-exhausted for '{model_name}'. Auto-falling back.")
                                break
                            continue
                        else:
                            # Per-minute RPM → soft rest, try next key
                            await self.rotator.mark_unhealthy(key, reason="rate_limit", session_id=session_id)
                            await asyncio.sleep(0.5)
                            continue

                    if category == "auth":
                        logger.warning(f"[TrinityBridge] Auth/Server Error for {model_name}. Rotating key...")
                        await self.rotator.mark_unhealthy(key, reason="auth_or_server", session_id=session_id)
                        continue

                    if category == "model_not_found":
                        logger.warning(f"[TrinityBridge] Model {model_name} không được hỗ trợ bởi Key hiện tại. Đang chuyển sang model dự phòng tiếp theo...")
                        break

                    logger.error(f"[TrinityBridge] Unknown AI Error for {model_name}: {e}")
                    continue

        logger.error(f"[TrinityBridge] Exhausted all keys and fallback models!")
        raise AIConfigurationError(
            f"Hệ thống AI đang tạm thời quá tải (Limit reached). Sếp vui lòng đợi 5-10 phút hoặc nâng cấp API Key nhé! Lỗi kỹ thuật: {str(last_error)}",
            models_to_try[-1] if models_to_try else "N/A",
            max_keys - 1
        )

    @asynccontextmanager
    async def run_stream(self, agent: Agent, prompt: str, **kwargs: object):
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
            daily_exhausted_count = 0
            for attempt in range(max_keys):
                key = await self.rotator.get_key(session_id=session_id)

                # V73.0: Skip (key+model) combos already known to be daily-exhausted
                if await self.rotator.is_model_daily_exhausted(key, model_name):
                    daily_exhausted_count += 1
                    if daily_exhausted_count >= max_keys:
                        logger.warning(f"[TrinityBridge][Stream] ALL keys daily-exhausted for model '{model_name}'. Falling back.")
                        break
                    continue

                model = self._create_model(model_name, api_key=key)

                try:
                    logger.info(f"[TrinityBridge][Stream] {model_name} (Attempt {attempt+1}/{max_keys}) (Session: {session_id})...")
                    
                    stream_started = False
                    try:
                        async with agent.run_stream(prompt, model=model, **kwargs) as stream:
                            stream_started = True
                            yield stream
                        
                        # Success: we yielded and the caller finished without exception
                        await self.rotator.set_success(key, session_id=session_id)
                        await self._save_sticky_model(model_name)
                        return
                    except Exception as inner_e:
                        if stream_started:
                            # CRITICAL: If stream already yielded, we CANNOT rotate.
                            # Re-raise to let caller handle it.
                            logger.error(f"[TrinityBridge][Stream] Error during stream consumption: {inner_e}")
                            raise inner_e
                        # Otherwise, fall through to rotation logic
                        raise inner_e

                except AIConfigurationError:
                    raise

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    category = self._classify_error(error_str)

                    # LOG DETAILED ERROR FOR DIAGNOSTICS
                    kid = self.rotator._get_key_id(key)
                    logger.error(f"[TrinityBridge][Stream] Model: {model_name} | Key: {key[:8]}... | KID: {kid} | Category: {category} | Details: {error_str}")

                    if "429 too many requests: hệ thống ai đang tạm thời đạt giới hạn an toàn" in error_str:
                        logger.error(f"[TrinityBridge][Stream] AI Engine overloaded, failing fast.")
                        raise AIConfigurationError(f"Hệ thống AI đang tạm thời vượt mức tải an toàn. Vui lòng thử lại sau 1 phút.", model_name, attempt)

                    if category == "fail_fast":
                        logger.error(f"[TrinityBridge][Stream] Non-rotatable error for {model_name}: {e}")
                        raise AIConfigurationError(f"AI Fail-Fast: {str(e)}", model_name, attempt)

                    if category == "rate_limit":
                        if self._is_daily_quota(error_str):
                            # V73.0: Per-(key, model) daily lock — key stays usable for other models!
                            await self.rotator.mark_model_daily(key, model_name)
                            daily_exhausted_count += 1
                            if daily_exhausted_count >= max_keys:
                                logger.warning(f"[TrinityBridge][Stream] ALL keys daily-exhausted for '{model_name}'. Auto-falling back.")
                                break
                            continue
                        else:
                            await self.rotator.mark_unhealthy(key, reason="rate_limit", session_id=session_id)
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
