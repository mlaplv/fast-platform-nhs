from __future__ import annotations
import logging
import asyncio
import os
import re
import time
import httpx
import sqlalchemy as sa
from typing import Optional, Union, cast, TYPE_CHECKING
from contextlib import asynccontextmanager
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.settings import ModelSettings
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.utils.http_client import SharedHttpClient
from .trinity_models import TrinityModels

if TYPE_CHECKING:
    from pydantic import BaseModel
    from pydantic_ai.run import AgentRunResult
    from pydantic_ai.result import StreamedRunResult

logger = logging.getLogger("api-gateway")

class AIConfigurationError(Exception):
    def __init__(self, message: str, model: Optional[str] = None, key_index: Optional[int] = None):
        super().__init__(message)
        self.model, self.key_index = model, (key_index + 1) if key_index is not None else None

_G_SAFETY_NONE = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

class TrinityBridge:
    """V65.0: Centralized AI Bridge. Modularized for Martial Law (<300 lines)."""
    def __init__(self) -> None:
        self.rotator: 'KeyRotator' = key_rotator
        self.primary_model: str = os.environ["AI_PRIMARY_MODEL"]
        self.fallback_model: str = os.environ["AI_FALLBACK_MODEL"]
        self.models_helper: TrinityModels = TrinityModels(self.rotator, self.primary_model, self.fallback_model)
        self.db_primary_model: Optional[str] = None
        self.db_waterfall: list[str] = []
        self.discovered: list[str] = []
        self._initialized: bool = False
        self.ROLE_FAST: str = "fast"
        self.ROLE_BRAIN: str = "brain"
        self._tenant_profile_cache: dict[str, tuple[Optional[str], list[str], float]] = {}
        
        # Elite V2.2: CPU Contention Guard (R4-Core Xeon Standard)
        # Prevents more than N concurrent heavy AI tasks from saturating the 4-core VPS.
        self.concurrency_guard: Optional[asyncio.Semaphore] = None

    @property
    def default_model_name(self) -> str:
        return self.db_primary_model or self.primary_model

    async def initialize(self) -> None:
        if not self._initialized:
            logger.info("📡 [TrinityBridge] Periodic Neural Bridge Initialization...")
            # Elite V2.2: Ensure keys are loaded if not already done (for non-lifespan entry points)
            if self.rotator.get_count() == 0:
                logger.info("🔑 [TrinityBridge] No keys detected in rotator. Initializing key loader...")
                await self.rotator.load_keys()

            # [R.C.3 FIX] Đồng bộ với run(): Semaphore(8) để tránh Queue Starvation với 8 API keys
            if self.concurrency_guard is None:
                self.concurrency_guard = asyncio.Semaphore(8)

            await self.reload_models()
            self._initialized = True
            logger.info(f"✅ [TrinityBridge] Neural Bridge ready. Models discovered: {len(self.discovered)}")


    async def reload_models(self) -> None:
        from backend.database.alchemy_config import alchemy_config
        from backend.database.models import VoiceProfile, User
        from sqlalchemy import select
        from backend.database.models import Role
        from backend.constants.tenants import APP_DOMAIN
        
        # Elite V2.2: Dynamic resolution to strictly avoid rule R00 hardcoding
        super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "admin@osmo.vn")
        
        maker = alchemy_config.create_session_maker()
        try:
            async with maker() as s:
                # Phase 1: Query by Role (SUPER_ADMIN) - sorted by latest updated to handle multiple admins
                p = (await s.execute(
                    select(VoiceProfile)
                    .join(User, User.id == VoiceProfile.user_id)
                    .join(User.roles)
                    .where(Role.code == "SUPER_ADMIN")
                    .order_by(VoiceProfile.updated_at.desc())
                    .limit(1)
                )).scalar_one_or_none()
                
                # Phase 2: Query by dynamic env variable config
                if not p:
                    p = (await s.execute(
                        select(VoiceProfile)
                        .join(User, User.id == VoiceProfile.user_id)
                        .where(User.email == super_admin_email)
                    )).scalar_one_or_none()
                
                # Phase 3: Query by active brand domain
                if not p:
                    p = (await s.execute(
                        select(VoiceProfile)
                        .join(User, User.id == VoiceProfile.user_id)
                        .where(User.email.like(f"%@{APP_DOMAIN}"))
                        .order_by(VoiceProfile.updated_at.desc())
                        .limit(1)
                    )).scalar_one_or_none()
                
                # Phase 4: Fallback to the absolute first profile
                if not p:
                    p = (await s.execute(select(VoiceProfile).order_by(VoiceProfile.updated_at.desc()).limit(1))).scalar_one_or_none()
                
                if p: 
                    self.db_primary_model = p.primary_model
                    self.db_waterfall = p.ai_models or []
                    logger.warning(f"🧬 [TrinityBridge] Loaded VoiceProfile configuration from DB (User: {p.id}): {self.db_primary_model} (Waterfall: {len(self.db_waterfall)} models)")
        except Exception as e: 
            logger.warning(f"⚠️ [TrinityBridge] Failed to load VoiceProfile: {e}")
        
        self.discovered = await self.models_helper.discover_available()

    async def get_tenant_profile(self) -> tuple[Optional[str], list[str]]:
        """
        Elite V2.2: Fetch VoiceProfile dynamically for the active tenant.
        Single-query JOIN — tránh N+1 gây CONNECTION_LEAK_WARNING.
        """
        from backend.database import current_tenant_id
        active_tenant = current_tenant_id.get() or "default"

        # CTO-Guided: Enable in-memory TTL caching only when not debugging
        is_debug = os.getenv("HELEN_DEBUG") == "1"
        now = time.time()
        if not is_debug and active_tenant in self._tenant_profile_cache:
            p_model, waterfall, expire_time = self._tenant_profile_cache[active_tenant]
            if now < expire_time:
                return p_model, waterfall

        if active_tenant == "default" and not current_tenant_id.get():
            return self.db_primary_model, self.db_waterfall

        try:
            from backend.database.alchemy_config import alchemy_config
            from backend.database.models import VoiceProfile, User, Role
            from sqlalchemy import select

            maker = alchemy_config.create_session_maker()
            async with maker() as s:
                # Single JOIN query: ưu tiên SUPER_ADMIN, fallback profile đầu tiên
                # Sắp xếp: SUPER_ADMIN role lên trước, sau đó theo updated_at DESC
                stmt = (
                    select(VoiceProfile)
                    .join(User, User.id == VoiceProfile.user_id)
                    .outerjoin(User.roles)
                    .where(User.tenant_id == active_tenant)
                    .order_by(
                        sa.case((Role.code == "SUPER_ADMIN", 0), else_=1),
                        VoiceProfile.updated_at.desc()
                    )
                    .limit(1)
                )
                p = (await s.execute(stmt)).scalar_one_or_none()
                if p:
                    res = (p.primary_model, p.ai_models or [])
                else:
                    res = (self.db_primary_model, self.db_waterfall)
                
                # Cache for 5 minutes (300 seconds)
                self._tenant_profile_cache[active_tenant] = (res[0], res[1], now + 300.0)
                return res
        except Exception as e:
            logger.warning(f"⚠️ [TrinityBridge] Failed to load tenant VoiceProfile for {active_tenant}: {e}")
            return self.db_primary_model, self.db_waterfall

    async def run(self, agent: Agent, prompt: Union[str, list], **kwargs: object) -> AgentRunResult:
        val_t: object = kwargs.pop("timeout", 90.0)
        t: float = float(val_t) if isinstance(val_t, (int, float)) else 90.0
        
        val_m: object = kwargs.pop("model", None)
        r_m: Optional[str] = str(val_m) if val_m is not None else None
        
        val_sid: object = kwargs.pop("session_id", None)
        s_id: Optional[str] = str(val_sid) if val_sid is not None else None
        
        val_role: object = kwargs.pop("role", None)
        role: Optional[str] = str(val_role) if val_role is not None else None
        
        val_force: object = kwargs.pop("force", False)
        force: bool = bool(val_force)
        
        val_pmt: object = kwargs.pop("per_model_timeout", None)
        pmt: Optional[float] = float(val_pmt) if val_pmt is not None else None
        
        # Elite V2.2: Mandatory Late-Initialization Guard (R45 - Cold Start Protection)
        if not self._initialized:
            await self.initialize()

        db_primary, db_waterfall = await self.get_tenant_profile()
        models = ([r_m] if r_m else []) + await self.models_helper.build_chain(role, db_primary, db_waterfall, self.discovered)
        
        # Elite V2.2: Final Fail-safe - If still empty, trigger urgent recovery
        if not models:
            logger.warning("🚨 [TrinityBridge] Zero models in chain. Triggering emergency re-discovery...")
            await self.reload_models()
            db_primary, db_waterfall = await self.get_tenant_profile()
            models = await self.models_helper.build_chain(role, db_primary, db_waterfall, self.discovered)

        # Dynamic default per-model timeout calculation
        if pmt is None:
            num_models = max(len(models), 1)
            pmt = max(10.0, min(t / num_models, 30.0))

        max_k, last_err = max(1, self.rotator.get_count()), None

        # [R.C.3 FIX] Tăng Semaphore 4→8 để phù hợp với 8 API keys.
        # Tránh tình trạng Queue Starvation khi nhiều request cùng chờ.
        if self.concurrency_guard is None:
            self.concurrency_guard = asyncio.Semaphore(8)

        # Extract shared parameters once (R110: Dependency Injection Support)
        system_prompt = kwargs.pop("system_prompt", None)
        deps = kwargs.pop("deps", None)
        model_settings_base = cast(dict[str, object], kwargs.pop("model_settings", {}))
        safety_none = bool(kwargs.pop("safety_none", False))

        start_time = time.time()
        _billing_quota_streak = 0

        for m_name in models:
            # Elite V2.2: Billing Quota Fast-Fail (all keys exhausted across consecutive models)
            if _billing_quota_streak >= 2:
                logger.error(f"🛑 [TrinityBridge] All-keys Billing Quota Exhausted ({_billing_quota_streak} consecutive models). Fast-failing.")
                break
            if self.models_helper.is_blacklisted(m_name):
                logger.debug(f"🛡️ [TrinityBridge] Blocking blacklisted model: {m_name}")
                continue
            rpm_fail_count = 0
            _model_billing_hit = False
            for att in range(max_k):
                if rpm_fail_count >= 3:
                    logger.warning(f"🛑 [TrinityBridge] Max RPM failures (3) for {m_name}. Skipping to fallback model.")
                    break
                key = None
                try:
                    # R105: Key discovery with strict safety
                    key = await self.rotator.get_key(model_name=m_name, session_id=s_id)
                    if not key:
                        continue
                    if not force and await self.rotator.is_model_daily_exhausted(key, m_name):
                        continue

                    shared_http_client = await SharedHttpClient.get_ai_client()
                    model_instance = GoogleModel(m_name, provider=GoogleProvider(api_key=key, http_client=shared_http_client))
                    ms = dict(model_settings_base)
                    if safety_none:
                        ms["google_safety_settings"] = _G_SAFETY_NONE

                    # Elite V2.2: Global Timeout Enforcement (prevents infinite waterfall loops)
                    remaining_t = t - (time.time() - start_time)
                    if remaining_t <= 0:
                        logger.error(f"🛑 [TrinityBridge] GLOBAL TIMEOUT EXCEEDED ({t}s) across all models. Bailing out.")
                        return None

                    attempt_timeout = min(remaining_t, pmt) if pmt is not None else remaining_t

                    # [R.C.3 FIX] Wrap BOTH semaphore acquisition and execution within asyncio.wait_for
                    # to prevent queue starvation from holding up requests past their timeout.
                    guard = self.concurrency_guard
                    assert guard is not None, "Concurrency guard is not initialized"

                    async def _execute_under_guard():
                        async with guard:
                            if system_prompt:
                                with agent.override(instructions=str(system_prompt)):
                                    return await agent.run(prompt, model=model_instance, model_settings=cast(ModelSettings, ms), deps=deps, **kwargs)
                            else:
                                return await agent.run(prompt, model=model_instance, model_settings=cast(ModelSettings, ms), deps=deps, **kwargs)

                    res = await asyncio.wait_for(_execute_under_guard(), timeout=attempt_timeout)

                    if hasattr(res, 'usage'):
                        await self.rotator.track_tokens(key, getattr(res.usage, 'total_tokens', 0))

                    await self.rotator.set_success(key, session_id=s_id)
                    await self.rotator.reset_model_failures(m_name)

                    # Elite V2.2: Standardized Result Extraction (Universal Wrapper Bypass)
                    if hasattr(res, 'data'):
                        logger.warning(f"📦 [TrinityBridge] Extraction (data): {type(res.data).__name__}")
                        # Debug: Check for annotations in the data
                        if hasattr(res.data, 'annotations') and not getattr(res.data, 'annotations'):
                            logger.warning(f"⚠️ [TrinityBridge] Model {m_name} returned EMPTY annotations!")
                        elif hasattr(res.data, 'seo_annotations') and not getattr(res.data, 'seo_annotations'):
                            logger.warning(f"⚠️ [TrinityBridge] Model {m_name} returned EMPTY seo_annotations!")
                        
                        return res.data
                    if hasattr(res, 'output'):
                        logger.warning(f"📦 [TrinityBridge] Extraction (output): {type(res.output).__name__}")
                        return res.output
                    return res

                except (asyncio.TimeoutError, TimeoutError, httpx.TimeoutException):
                    last_err = "Timeout"
                    logger.warning(f"[TrinityBridge] Model '{m_name}' timed out after {attempt_timeout:.1f}s. Breaking to next model waterfall.")
                    # Timeout is a model-level capacity/slowness issue, NOT an API key issue.
                    # We do not penalize the key (avoiding premature cooldowns).
                    await self.rotator.track_model_failure(m_name, reason="timeout")
                    break
                except Exception as e:
                    last_err = e
                    err_msg = str(e).lower()
                    if "quota/cooldown: no keys" in err_msg or "auth_error: all keys blacklisted" in err_msg:
                        logger.warning(f"⏳ [TrinityBridge] No keys available for model {m_name}. Waterfalling to next model...")
                        break
                    cat = self.models_helper.classify_error(err_msg)

                    # Elite V2.2: Professional Concise Logging
                    if cat == "rate_limit":
                        retry_match = re.search(r"retry in ([\d\.]+)s", err_msg)
                        wait_info = f" (Retry in {retry_match.group(1)}s)" if retry_match else ""
                        
                        if "resource_exhausted" in str(e).upper() or "QUOTA" in str(e).upper():
                            if self.models_helper.is_daily_quota(str(e)):
                                logger.warning(f"⚡ [TrinityBridge] Daily Quota Exhausted: {m_name}{wait_info}. Marking as daily.")
                                await self.rotator.mark_model_daily(key, m_name)
                                _model_billing_hit = True
                                break
                            else:
                                logger.warning(f"⏳ [TrinityBridge] Rate Limit (RPM) hit: {m_name}{wait_info}. Rotating key...")
                                await self.rotator.mark_unhealthy(key, reason="rate_limit", session_id=s_id)
                                rpm_fail_count += 1
                                continue
                        else:
                            logger.warning(f"🛰️ [TrinityBridge] Service Unavailable (503/500) on {m_name}. Breaking to next model waterfall.")
                            await self.rotator.track_model_failure(m_name, reason="503_unavailable")
                            break

                    if cat == "fail_fast":
                        logger.error(f"🚫 [TrinityBridge] Fail-Fast: {m_name} | {str(e)[:100]}...")
                        await self.rotator.mark_model_poisoned(m_name, reason=f"fail_fast: {str(e)[:50]}")
                        break
                    
                    if cat == "model_not_found":
                        logger.error(f"🔍 [TrinityBridge] Model Not Found (404): {m_name}. Persistent Blacklisting...")
                        await self.models_helper.add_to_persistent_blacklist(m_name, reason="404")
                        break

                    # For all other errors, use standard logging
                    logger.warning(f"⚠️ [TrinityBridge] Model '{m_name}' error: {str(e)[:200]}")
                    
                    if "validation" in err_msg or "exceeded maximum output retries" in err_msg or "unexpectedmodelbehavior" in err_msg:
                        logger.warning(f"⚠️ [TrinityBridge] Model {m_name} failed output validation/retries. Breaking to next model waterfall...")
                        break
                    
                    if cat == "tool_unsupported":
                        break
                    if not key:
                        continue

                    if cat == "auth_hard":
                        await self.rotator.mark_unhealthy(key, reason="auth_hard", session_id=s_id)
                        continue
                    if cat == "auth_soft":
                        # Project-level denial affects ALL keys — break to next model immediately
                        if "denied access" in err_msg or "project disabled" in err_msg:
                            logger.error(f"🚫 [TrinityBridge] Project-level 403 on {m_name}. Breaking to next model.")
                            await self.rotator.track_model_failure(m_name, reason="project_denied")
                            break
                        await self.rotator.mark_unhealthy(key, reason="auth_soft", session_id=s_id)
                        continue
                        
                    # Catch-all for other errors
                    await self.rotator.mark_unhealthy(key, reason="unknown", session_id=s_id)

            # Elite V2.2: Billing Quota Fast-Fail Tracker
            if _model_billing_hit:
                _billing_quota_streak += 1
            else:
                _billing_quota_streak = 0

        raise AIConfigurationError(f"AI Overloaded: {last_err}", str(models[-1]) if models else "N/A", max_k-1)

    @asynccontextmanager
    async def run_stream(self, agent: Agent, prompt: str, **kwargs: object) -> StreamedRunResult:
        start_time = time.time()
        val_t: object = kwargs.pop("timeout", 90.0)
        t: float = float(val_t) if isinstance(val_t, (int, float)) else 90.0
        val_pmt: object = kwargs.pop("per_model_timeout", None)
        pmt: Optional[float] = float(val_pmt) if val_pmt is not None else None

        val_m: object = kwargs.pop("model", None)
        r_m: Optional[str] = str(val_m) if val_m is not None else None
        
        val_sid: object = kwargs.pop("session_id", None)
        s_id: Optional[str] = str(val_sid) if val_sid is not None else None
        
        val_role: object = kwargs.pop("role", None)
        role: Optional[str] = str(val_role) if val_role is not None else None
        
        val_force: object = kwargs.pop("force", False)
        force: bool = bool(val_force)
        
        # Elite V2.2: Mandatory Late-Initialization Guard (R45 - Cold Start Protection)
        if not self._initialized:
            await self.initialize()

        models = ([r_m] if r_m else []) + await self.models_helper.build_chain(role, self.db_primary_model, self.db_waterfall, self.discovered)
        
        # Elite V2.2: Final Fail-safe - If still empty, trigger urgent recovery
        if not models:
            logger.warning("🚨 [TrinityBridge] Zero models in stream chain. Triggering emergency re-discovery...")
            await self.reload_models()
            models = await self.models_helper.build_chain(role, self.db_primary_model, self.db_waterfall, self.discovered)

        # Dynamic default per-model timeout calculation
        if pmt is None:
            num_models = max(len(models), 1)
            pmt = max(10.0, min(t / num_models, 30.0))

        max_k, last_err = max(1, self.rotator.get_count()), None

        if self.concurrency_guard is None: self.concurrency_guard = asyncio.Semaphore(8)

        # Extract shared parameters once (R110)
        system_prompt = kwargs.pop("system_prompt", None)
        deps = kwargs.pop("deps", None)
        model_settings_base = cast(dict[str, object], kwargs.pop("model_settings", {}))
        safety_none = bool(kwargs.pop("safety_none", False))

        for m_name in models:
            if self.models_helper.is_blacklisted(m_name):
                logger.debug(f"🛡️ [TrinityBridge] Blocking blacklisted model (Stream): {m_name}")
                continue
            rpm_fail_count = 0
            for att in range(max_k):
                if rpm_fail_count >= 3:
                    logger.warning(f"🛑 [TrinityBridge] Max RPM failures (Stream) (3) for {m_name}. Skipping to fallback model.")
                    break
                key = None
                try:
                    key = await self.rotator.get_key(model_name=m_name, session_id=s_id)
                    if not key: continue
                    if not force and await self.rotator.is_model_daily_exhausted(key, m_name): continue
                    shared_http_client = await SharedHttpClient.get_ai_client()
                    
                    # Calculate attempt_timeout for this stream attempt
                    remaining_t = t - (time.time() - start_time)
                    if remaining_t <= 0:
                        logger.error(f"🛑 [TrinityBridge] GLOBAL TIMEOUT EXCEEDED ({t}s) across all models (Stream). Bailing out.")
                        break
                    attempt_timeout = min(remaining_t, pmt) if pmt is not None else remaining_t

                    guard = self.concurrency_guard
                    assert guard is not None, "Concurrency guard is not initialized"

                    try:
                        await asyncio.wait_for(guard.acquire(), timeout=attempt_timeout)
                    except asyncio.TimeoutError:
                        logger.warning(f"[TrinityBridge] Semaphore acquisition timed out for stream {m_name} after {attempt_timeout:.1f}s.")
                        await self.rotator.track_model_failure(m_name, reason="timeout")
                        break

                    try:
                        model_instance = GoogleModel(m_name, provider=GoogleProvider(api_key=key, http_client=shared_http_client))
                        ms = dict(model_settings_base)
                        if safety_none: ms["google_safety_settings"] = _G_SAFETY_NONE
                        
                        if system_prompt:
                            with agent.override(instructions=str(system_prompt)):
                                async with agent.run_stream(prompt, model=model_instance, model_settings=cast(ModelSettings, ms), deps=deps, **kwargs) as stream:
                                    yield stream
                        else:
                            async with agent.run_stream(prompt, model=model_instance, model_settings=cast(ModelSettings, ms), deps=deps, **kwargs) as stream:
                                yield stream
                    finally:
                        guard.release()
                    
                    await self.rotator.set_success(key, session_id=s_id)
                    await self.rotator.reset_model_failures(m_name)
                    return
                except (asyncio.TimeoutError, TimeoutError, httpx.TimeoutException):
                    last_err = "Timeout"
                    logger.warning(f"[TrinityBridge] Model '{m_name}' timed out during stream. Breaking to next model waterfall.")
                    await self.rotator.track_model_failure(m_name, reason="timeout")
                    break
                except Exception as e:
                    last_err = e
                    err_msg = str(e).lower()
                    if "quota/cooldown: no keys" in err_msg or "auth_error: all keys blacklisted" in err_msg:
                        logger.warning(f"⏳ [TrinityBridge] No keys available for model {m_name} (Stream). Waterfalling to next model...")
                        break
                    cat = self.models_helper.classify_error(err_msg)

                    if not key: continue

                    if cat == "rate_limit":
                        retry_match = re.search(r"retry in ([\d\.]+)s", err_msg)
                        wait_info = f" (Retry in {retry_match.group(1)}s)" if retry_match else ""
                        
                        if "resource_exhausted" in str(e).upper() or "QUOTA" in str(e).upper():
                            logger.warning(f"⚡ [TrinityBridge] Quota Exhausted (Stream): {m_name}{wait_info}. Rotating key...")
                            await self.rotator.mark_model_daily(key, m_name)
                            continue
                        else:
                            logger.warning(f"🛰️ [TrinityBridge] Service Unavailable (503/500) on {m_name} (Stream). Breaking to next model waterfall.")
                            await self.rotator.track_model_failure(m_name, reason="stream_error")
                            break

                    if cat == "auth_hard": 
                        await self.rotator.mark_unhealthy(key, reason="auth_hard", session_id=s_id)
                        continue
                    if cat == "auth_soft":
                        if "denied access" in err_msg or "project disabled" in err_msg:
                            logger.error(f"🚫 [TrinityBridge] Project-level 403 on {m_name} (Stream). Breaking to next model.")
                            await self.rotator.track_model_failure(m_name, reason="project_denied")
                            break
                        await self.rotator.mark_unhealthy(key, reason=cat, session_id=s_id)
                        continue
                    
                    if cat == "model_not_found":
                        logger.error(f"🔍 [TrinityBridge] Model Not Found (404): {m_name}. Persistent Blacklisting...")
                        await self.models_helper.add_to_persistent_blacklist(m_name, reason="404")
                        break
                        
                    logger.warning(f"⚠️ [TrinityBridge] Stream error '{m_name}': {str(e)[:150]}")
                    if "validation" in err_msg or "exceeded maximum output retries" in err_msg or "unexpectedmodelbehavior" in err_msg:
                        logger.warning(f"⚠️ [TrinityBridge] Stream model {m_name} failed output validation/retries. Breaking to next model waterfall...")
                        break
                    await self.rotator.mark_unhealthy(key, reason="unknown", session_id=s_id)
        raise AIConfigurationError(f"Stream Overloaded: {last_err}")

    def _provision_model(self, m_name: str, key: str, params: dict[str, object]) -> tuple[GoogleModel, dict[str, object]]:
        """Elite V2.2: Centralized Model Provisioning Factory (Structural Repair)."""
        if not key:
            raise AIConfigurationError(f"Model {m_name} requested but key is EMPTY. Check rotators.")

        # Pass-by-reference: Modifying 'params' removes custom keys from caller's kwargs
        val_sn = params.pop("safety_none", False)
        s_settings = _G_SAFETY_NONE if bool(val_sn) else None
        
        model = GoogleModel(
            m_name, 
            provider=GoogleProvider(api_key=key),
        )
        
        # Pop model_settings to avoid double-passing to PydanticAI
        ms = cast(dict[str, object], params.pop("model_settings", {}))
        if s_settings: 
            ms["google_safety_settings"] = s_settings
            
        return model, ms

trinity_bridge: TrinityBridge = TrinityBridge()
