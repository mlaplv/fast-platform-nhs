import logging
import os
import asyncio
import httpx
from typing import Optional, List, Dict
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
        # Default hardcoded fallbacks if DB is empty
        self.default_model_name = "gemini-2.5-flash"
        self.fallback_model_name = "gemini-3.1-pro-preview"

        # Dynamic Model Pool (V75)
        self.db_primary_model = None
        self.db_waterfall = []

        # NOTE: Model waterfall is now managed primarily via DB (VoiceProfile).
        self.model_waterfall = []

        self.success_model_key = "ai:bridge:last_success_model"

        # Initial load state
        self._initialized = False
        self._discovered_cache = []

        # Roles (V75)
        self.ROLE_FAST = "fast"   # Flash/Lite models
        self.ROLE_BRAIN = "brain" # Pro models

    async def initialize(self):
        """Explicit initialization for lifespan hooks (V76)."""
        if not self._initialized:
            await self.reload_models()
            self._initialized = True

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
        
        # V75: Autonomous Refresh
        await self._discover_models()

    async def _discover_models(self):
        """Live Discovery: Query Google for actually available models."""
        cached = await self.rotator.get_discovered_models()
        if cached:
            self._discovered_cache = cached
            return

        # Try with a healthy key
        key = ""
        try:
            key = await self.rotator.get_key()
        except:
            return

        if not key: return

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    all_raw_models = data.get("models", [])
                    models = [m["name"].replace("models/", "") for m in all_raw_models 
                             if "generateContent" in (m.get("supportedGenerationMethods") or [])]
                    
                    self._discovered_cache = models
                    await self.rotator.save_discovered_models(models)
                    logger.info(f"[TrinityBridge] Discovery Successful. Found {len(models)} usable models.")
                else:
                    logger.warning(f"[TrinityBridge] Discovery Failed ({resp.status_code}): {resp.text[:100]}")
        except Exception as e:
            logger.error(f"[TrinityBridge] Discovery Exception: {e}")
            print(f"[DEBUG] Discovery Exception: {e}")

    def _get_role_models(self, role: str) -> list[str]:
        """Strategic Mapping: Find best available models for a role."""
        if not self._discovered_cache:
            return []
        
        if role == self.ROLE_FAST:
            # Prefer Flash -> Flash-Lite -> Flash-8b
            potential = ["flash-lite", "flash-8b", "flash"]
        else:
            # Prefer Pro -> Brain (future)
            potential = ["pro", "brain"]

        results = []
        for p in potential:
            for m in self._discovered_cache:
                if p in m.lower():
                    results.append(m)
        
        # Sort by 'latest' or 'version' if possible (crude string sort)
        results.sort(reverse=True)
        return results

    async def _build_model_chain(self, role: Optional[str] = None) -> list[str]:
        """
        Build priority model chain (shared between run and run_stream).
        CNS V76: Role-Based Prioritization added.
        """
        raw_models = []
        
        # 1. DB Priority (V75)
        if self.db_primary_model:
            raw_models.append(self.db_primary_model)
        if self.db_waterfall:
            for m in self.db_waterfall:
                if m not in raw_models:
                    raw_models.append(m)

        # 2. Waterfall ENV Priority
        if self.model_waterfall:
            for m in self.model_waterfall:
                if m not in raw_models:
                    raw_models.append(m)
        
        # 3. Default ENV Fallbacks
        if self.default_model_name not in raw_models:
            raw_models.append(self.default_model_name)
        if self.fallback_model_name and self.fallback_model_name not in raw_models:
            raw_models.append(self.fallback_model_name)

        # 4. Autonomous Discovery Integration (V75)
        brain_models = self._get_role_models(self.ROLE_BRAIN)
        fast_models = self._get_role_models(self.ROLE_FAST)
        
        for m in (brain_models + fast_models):
            if m not in raw_models:
                raw_models.append(m)

        # CNS V76: Role-Based Intelligence Injector
        # We reorganize the list based on keywords if a role is provided
        if role:
            prioritized = []
            others = []
            
            if role == self.ROLE_FAST:
                # Mechanically fast/cheap keywords (prioritize lite)
                keywords = ["lite", "8b", "flash"]
            elif role == self.ROLE_BRAIN:
                # Creative high-IQ keywords
                keywords = ["pro", "ultra", "brain", "creative"]
            else:
                keywords = []

            for m in raw_models:
                if any(k in m.lower() for k in keywords):
                    prioritized.append(m)
                else:
                    others.append(m)
            
            # Reassemble with role-specific models at the top
            raw_models = prioritized + others

        # V75.1: Filter out Poisoned models
        healthy_models = []
        for m in raw_models:
            if not await self.rotator.is_model_poisoned(m):
                healthy_models.append(m)
        
        return healthy_models

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
        if not api_key:
            logger.error(f"[TrinityBridge] CRITICAL: api_key is EMPTY for model {model_name}")
            raise AIConfigurationError(f"API Key is missing for {model_name}")

        logger.info(f"[TrinityBridge] Creating model {model_name} with key: {api_key[:8]}...")
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
        role = kwargs.pop("role", None)

        models_to_try = []
        if requested_model:
            models_to_try.append(requested_model)

        base_chain = await self._build_model_chain(role=role)
        sticky_model = await self._get_sticky_model()

        if sticky_model and sticky_model not in models_to_try:
            models_to_try.append(sticky_model)
        for m in base_chain:
            if m not in models_to_try:
                models_to_try.append(m)

        max_keys = max(1, self.rotator.get_count())

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
                        logger.warning(f"[TrinityBridge] Model {model_name} không được hỗ trợ hoặc đã bị xóa. Đang chuyển sang model khác...")
                        await self.rotator.mark_model_poisoned(model_name, reason="404")
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
        role = kwargs.pop("role", None)

        models_to_try = []
        if requested_model:
            models_to_try.append(requested_model)

        base_chain = await self._build_model_chain(role=role)
        sticky_model = await self._get_sticky_model()

        if sticky_model and sticky_model not in models_to_try:
            models_to_try.append(sticky_model)
        for m in base_chain:
            if m not in models_to_try:
                models_to_try.append(m)

        max_keys = max(1, self.rotator.get_count())
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
                        logger.warning(f"[TrinityBridge][Stream] Model {model_name} not found. Poisoning model and jumping...")
                        await self.rotator.mark_model_poisoned(model_name, reason="404")
                        break

                    logger.error(f"[TrinityBridge][Stream] Unknown AI Error: {e}")
                    continue

        raise AIConfigurationError(f"Hệ thống AI đang tạm thời quá tải cho Stream. Sếp vui lòng đợi 5-10 phút nhé! Lỗi kỹ thuật: {str(last_error)}")

trinity_bridge = TrinityBridge()
