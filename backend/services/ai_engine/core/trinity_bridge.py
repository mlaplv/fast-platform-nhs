import logging
import asyncio
from typing import Optional, List, Dict
from contextlib import asynccontextmanager
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from backend.services.ai_engine.core.key_rotator import key_rotator
from .trinity_models import TrinityModels

logger = logging.getLogger("api-gateway")

class AIConfigurationError(Exception):
    def __init__(self, message: str, model: Optional[str] = None, key_index: Optional[int] = None):
        super().__init__(message)
        self.model, self.key_index = model, (key_index + 1) if key_index is not None else None

class TrinityBridge:
    """V65.0: Centralized AI Bridge. Modularized for Martial Law (<300 lines)."""
    def __init__(self):
        self.rotator = key_rotator
        self.models_helper = TrinityModels(self.rotator, "gemini-2.0-flash", "gemini-1.5-pro")
        self.db_primary_model, self.db_waterfall, self.discovered, self._initialized = None, [], [], False
        self.ROLE_FAST, self.ROLE_BRAIN = "fast", "brain"

    async def initialize(self):
        if not self._initialized: await self.reload_models(); self._initialized = True

    async def reload_models(self):
        from backend.database.alchemy_config import alchemy_config
        from backend.database.models import VoiceProfile
        from sqlalchemy import select
        maker = alchemy_config.create_session_maker()
        try:
            async with maker() as s:
                p = (await s.execute(select(VoiceProfile).limit(1))).scalar_one_or_none()
                if p: self.db_primary_model, self.db_waterfall = p.primary_model, p.ai_models or []
        except: pass
        self.discovered = await self.models_helper.discover_available()

    async def run(self, agent: Agent, prompt: str, **kwargs: object):
        t, r_m, s_id, role = kwargs.pop("timeout", 90.0), kwargs.pop("model", None), kwargs.pop("session_id", None), kwargs.pop("role", None)
        force = kwargs.pop("force", False)
        models = ([r_m] if r_m else []) + await self.models_helper.build_chain(role, self.db_primary_model, self.db_waterfall, self.discovered)
        max_k, last_err = max(1, self.rotator.get_count()), None

        for m_name in models:
            for att in range(max_k):
                key = None
                try:
                    # R105: Key discovery with strict safety
                    key = await self.rotator.get_key(model_name=m_name, session_id=s_id)
                    if not key: continue
                    if not force and await self.rotator.is_model_daily_exhausted(key, m_name): continue
                    
                    logger.info(f"[TrinityBridge] {m_name} (Att {att+1}/{max_k}) (S: {s_id})")
                    res = await asyncio.wait_for(agent.run(prompt, model=GoogleModel(m_name, provider=GoogleProvider(api_key=key)), **kwargs), timeout=t)
                    
                    if hasattr(res, 'usage'): await self.rotator.track_tokens(key, getattr(res.usage, 'total_tokens', 0))
                    await self.rotator.set_success(key, session_id=s_id)
                    return res
                except (asyncio.TimeoutError, TimeoutError): last_err = "Timeout"; break
                except Exception as e:
                    last_err, cat = e, self.models_helper.classify_error(str(e))
                    if cat == "fail_fast": raise AIConfigurationError(f"AI Fail-Fast: {e}", m_name, att)
                    if cat == "tool_unsupported": break
                    if not key: continue # Cannot mark unhealthy if we don't have a key
                    if cat == "rate_limit":
                        if self.models_helper.is_daily_quota(str(e)): await self.rotator.mark_model_daily(key, m_name); continue
                        await self.rotator.mark_unhealthy(key, reason="rate_limit", session_id=s_id); continue
                    if cat == "auth": await self.rotator.mark_unhealthy(key, reason="auth", session_id=s_id); continue
                    if cat == "model_not_found": await self.rotator.mark_model_poisoned(m_name, reason="404"); break
        raise AIConfigurationError(f"AI Overloaded: {last_err}", models[-1] if models else "N/A", max_k-1)

    @asynccontextmanager
    async def run_stream(self, agent: Agent, prompt: str, **kwargs: object):
        r_m, s_id, role = kwargs.pop("model", None), kwargs.pop("session_id", None), kwargs.pop("role", None)
        force = kwargs.pop("force", False)
        models = ([r_m] if r_m else []) + await self.models_helper.build_chain(role, self.db_primary_model, self.db_waterfall, self.discovered)
        max_k, last_err = max(1, self.rotator.get_count()), None

        for m_name in models:
            for att in range(max_k):
                key = None
                try:
                    key = await self.rotator.get_key(model_name=m_name, session_id=s_id)
                    if not key: continue
                    if not force and await self.rotator.is_model_daily_exhausted(key, m_name): continue
                    async with agent.run_stream(prompt, model=GoogleModel(m_name, provider=GoogleProvider(api_key=key)), **kwargs) as stream:
                        yield stream
                    await self.rotator.set_success(key, session_id=s_id); return
                except Exception as e:
                    last_err, cat = e, self.models_helper.classify_error(str(e))
                    if not key: continue
                    if cat == "rate_limit" and self.models_helper.is_daily_quota(str(e)): await self.rotator.mark_model_daily(key, m_name); continue
                    if cat in ["rate_limit", "auth"]: await self.rotator.mark_unhealthy(key, reason=cat, session_id=s_id); continue
                    if cat == "model_not_found": await self.rotator.mark_model_poisoned(m_name, reason="404"); break
        raise AIConfigurationError(f"Stream Overloaded: {last_err}")

trinity_bridge = TrinityBridge()
