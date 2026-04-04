from __future__ import annotations
import logging
import asyncio
import os
from typing import Optional, Union, cast, TYPE_CHECKING
from contextlib import asynccontextmanager
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.settings import ModelSettings
from backend.services.ai_engine.core.key_rotator import key_rotator
from .trinity_models import TrinityModels

if TYPE_CHECKING:
    from pydantic import BaseModel

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
    def __init__(self):
        self.rotator = key_rotator
        self.primary_model = os.getenv("AI_PRIMARY_MODEL", "gemini-2.0-flash")
        self.fallback_model = os.getenv("AI_FALLBACK_MODEL", "gemini-1.5-pro")
        self.models_helper = TrinityModels(self.rotator, self.primary_model, self.fallback_model)
        self.db_primary_model, self.db_waterfall, self.discovered, self._initialized = None, [], [], False
        self.ROLE_FAST, self.ROLE_BRAIN = "fast", "brain"

    @property
    def default_model_name(self) -> str:
        return self.db_primary_model or self.primary_model

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
        val_t = kwargs.pop("timeout", 90.0)
        t = float(val_t) if isinstance(val_t, (int, float)) else 90.0
        
        val_m = kwargs.pop("model", None)
        r_m = str(val_m) if val_m is not None else None
        
        val_sid = kwargs.pop("session_id", None)
        s_id = str(val_sid) if val_sid is not None else None
        
        val_role = kwargs.pop("role", None)
        role = str(val_role) if val_role is not None else None
        
        val_force = kwargs.pop("force", False)
        force = bool(val_force)
        
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
                    system_prompt = kwargs.pop("system_prompt", None)
                    
                    # Elite V2.2: Unified Model Provisioning (Pass-by-Reference for 1.77.0 Safety)
                    model_instance, ms = self._provision_model(m_name, key, kwargs)
                    
                    if system_prompt:
                        with agent.override(instructions=str(system_prompt)):
                            res = await asyncio.wait_for(agent.run(prompt, model=model_instance, model_settings=cast(ModelSettings, ms), **kwargs), timeout=t)
                    else:
                        res = await asyncio.wait_for(agent.run(prompt, model=model_instance, model_settings=cast(ModelSettings, ms), **kwargs), timeout=t)
                    
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
                        if "QUOTA/COOLDOWN" in str(e):
                            logger.info(f"[TrinityBridge] Model '{m_name}' has NO keys available. Skipping model.")
                            break # Move to next model immediately!
                        if self.models_helper.is_daily_quota(str(e)) and key:
                            await self.rotator.mark_model_daily(key, m_name)
                        continue
                    if cat == "auth": await self.rotator.mark_unhealthy(key, reason="auth", session_id=s_id); continue
                    if cat == "model_not_found": await self.rotator.mark_model_poisoned(m_name, reason="404"); break
        raise AIConfigurationError(f"AI Overloaded: {last_err}", str(models[-1]) if models else "N/A", max_k-1)

    @asynccontextmanager
    async def run_stream(self, agent: Agent, prompt: str, **kwargs: object):
        val_m = kwargs.pop("model", None)
        r_m = str(val_m) if val_m is not None else None
        
        val_sid = kwargs.pop("session_id", None)
        s_id = str(val_sid) if val_sid is not None else None
        
        val_role = kwargs.pop("role", None)
        role = str(val_role) if val_role is not None else None
        
        val_force = kwargs.pop("force", False)
        force = bool(val_force)
        
        models = ([r_m] if r_m else []) + await self.models_helper.build_chain(role, self.db_primary_model, self.db_waterfall, self.discovered)
        max_k, last_err = max(1, self.rotator.get_count()), None

        for m_name in models:
            for att in range(max_k):
                key = None
                try:
                    key = await self.rotator.get_key(model_name=m_name, session_id=s_id)
                    if not key: continue
                    if not force and await self.rotator.is_model_daily_exhausted(key, m_name): continue
                    
                    system_prompt = kwargs.pop("system_prompt", None)
                    
                    # Elite V2.2: Unified Model Provisioning (Streaming)
                    model_instance, ms = self._provision_model(m_name, key, kwargs)
                    
                    if system_prompt:
                        with agent.override(instructions=str(system_prompt)):
                            async with agent.run_stream(prompt, model=model_instance, model_settings=cast(ModelSettings, ms), **kwargs) as stream:
                                yield stream
                    else:
                        async with agent.run_stream(prompt, model=model_instance, model_settings=cast(ModelSettings, ms), **kwargs) as stream:
                            yield stream
                    await self.rotator.set_success(key, session_id=s_id); return
                except Exception as e:
                    last_err, cat = e, self.models_helper.classify_error(str(e))
                    if not key: continue
                    if cat == "rate_limit" and self.models_helper.is_daily_quota(str(e)): await self.rotator.mark_model_daily(key, m_name); continue
                    if cat in ["rate_limit", "auth"]: await self.rotator.mark_unhealthy(key, reason=cat, session_id=s_id); continue
                    if cat == "model_not_found": await self.rotator.mark_model_poisoned(m_name, reason="404"); break
        raise AIConfigurationError(f"Stream Overloaded: {last_err}")

    def _provision_model(self, m_name: str, key: str, params: dict[str, object]) -> tuple[GoogleModel, dict[str, object]]:
        """Elite V2.2: Centralized Model Provisioning Factory (Structural Repair)."""
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

trinity_bridge = TrinityBridge()
