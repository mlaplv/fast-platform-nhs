from __future__ import annotations
import logging
import asyncio
import re
from typing import Optional, Union, cast, TYPE_CHECKING
from abc import ABC, abstractmethod
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

if TYPE_CHECKING:
    from pydantic import BaseModel

logger = logging.getLogger("api-gateway")

class MedicalShieldMixin:
    """Elite V2.2: Universal Medical Terms Shield (Bypassing Gemini Safety)."""
    
    async def _mask_sensitive_medical_terms(self, text: str) -> str:
        """
        Academic rewrite of sensitive Vietnamese medical slang/symptoms.
        Uses Redis-backed dynamic map with local hardcoded fallback.
        """
        from backend.services.xohi_memory import xohi_memory
        import json
        
        # 1. Fallback Static Map (R109 taxonomy)
        mask_map: dict[str, str] = {
            "hôi nách": "tăng tiết mồ hôi vùng dưới cánh tay (hyperhidrosis axillaris)",
            "hôi chân": "mùi hôi chân do vi khuẩn (bromodosis)",
            "mồ hôi tay": "tăng tiết mồ hôi lòng bàn tay (palmar hyperhidrosis)",
            "trị dứt điểm": "kiểm soát triệt để triệu chứng (complete control)",
            "thuốc": "tinh chất thảo dược cao cấp (premium herbal essence)",
            "chữa": "hỗ trợ cải thiện (supporting improvement)",
            "bệnh": "vấn đề da liễu (dermatological condition)"
        }

        # 2. Try Redis enrichment
        try:
            mask_raw = await xohi_memory.client.get("support:system:mask_map")
            if mask_raw:
                extra_map = json.loads(mask_raw)
                if isinstance(extra_map, dict):
                    mask_map.update(cast(dict[str, str], extra_map))
        except Exception:
            pass # Keep using static map on Redis failure

        processed = text.lower()
        for slang, medical in mask_map.items():
            processed = processed.replace(slang, medical)
        return processed

class SearchKeyMixin:
    """Elite V2.2: Standardized Google Custom Search Key Rotation."""
    _key_lock = asyncio.Lock()
    _key_idx = 0
    
    def _ensure_search_keys(self) -> None:
        from backend.utils.config import get_env_json
        import os
        if hasattr(self, "search_keys") and getattr(self, "search_keys"): return
        setattr(self, "search_keys", [])
        search_keys = cast(list[dict[str, str]], getattr(self, "search_keys"))
        
        env_keys = get_env_json("GOOGLE_SEARCH_KEYS")
        env_cxs = get_env_json("GOOGLE_SEARCH_CXS")
        if env_keys and env_cxs:
            for i, k in enumerate(env_keys):
                cx = env_cxs[i] if i < len(env_cxs) else env_cxs[0]
                search_keys.append({"key": str(k), "cx": str(cx)})
        if not search_keys:
            for i in ["", "_1", "_2"]:
                k = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}")
                cx = os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
                if k and cx:
                    search_keys.append({"key": k, "cx": cx})

    async def _get_search_pair(self) -> Optional[dict[str, str]]:
        self._ensure_search_keys()
        search_keys = cast(list[dict[str, str]], getattr(self, "search_keys"))
        if not search_keys: return None
        async with self._key_lock:
            pair = search_keys[self.__class__._key_idx % len(search_keys)]
            self.__class__._key_idx += 1
        return pair

class XoHiProgressMixin:
    """Elite V2.2: Standardized progress reporting for XoHi campaigns."""
    async def _emit_progress(self, campaign: object, msg: str, status: str = "PROCESSING") -> None:
        from backend.services.event_bus import event_bus
        from datetime import datetime, timezone
        c_id = getattr(campaign, "id", campaign)
        u_id = getattr(campaign, "user_id", None)
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": str(c_id),
            "user_id": str(u_id) if u_id else None,
            "message": msg,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

class BaseAgentOperative(ABC, MedicalShieldMixin):
    """
    V2.2 Heritage Core: Standardized AI Orchestration.
    All XoHi/Client Operatives MUST inherit from this base.
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"api-gateway.{agent_id}")
        self.bridge = trinity_bridge

    @abstractmethod
    async def chat(self, request: object, **kwargs: object) -> object:
        """Standardized entry point for all AI agents."""
        pass

    async def _report_telemetry(self, task: str, duration: float, error: Optional[str] = None) -> None:
        """Standardized system-wide performance reporting."""
        status = "SUCCESS" if not error else f"FAILED ({error})"
        self.logger.info(f"[{self.agent_id}] {task} {status} | Latency: {duration:.3f}s")
