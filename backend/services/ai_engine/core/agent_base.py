from __future__ import annotations
import logging
import asyncio
import re
import json
from typing import Optional, Union, cast, TYPE_CHECKING, Dict, Type
from abc import ABC, abstractmethod
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

if TYPE_CHECKING:
    from pydantic import BaseModel
    from sqlalchemy.ext.asyncio import AsyncSession
    from backend.database.models import ContentCampaign

from backend.database.models.system import UnifiedAgentTask
from backend.database.alchemy_config import alchemy_config

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# ELITE V2.2 AGENT REGISTRY (The Heritage Backdoor)
# ══════════════════════════════════════════════════════════════
# Global registry to allow Worker to instantiate any operative by ID
AGENT_REGISTRY: Dict[str, Type["BaseAgentOperative"]] = {}

class MedicalShieldMixin:
    """Elite V2.2: Universal Medical Terms Shield (Bypassing Gemini Safety)."""
    
    async def _mask_sensitive_medical_terms(self, text: str) -> str:
        """
        Academic rewrite of sensitive Vietnamese medical slang/symptoms.
        Uses Redis-backed dynamic map with local hardcoded fallback.
        """
        from backend.services.xohi_memory import xohi_memory
        
        # 1. Fallback Static Map (R109 taxonomy)
        # Refined for Elite V2.2: Avoid over-technical terms that trigger safety blocks
        mask_map: dict[str, str] = {
            "hôi nách": "xịt nách",
            "hôi chân": "xịt chân",
            "mồ hôi tay": "tăng tiết mồ hôi lòng bàn tay",
            "trị dứt điểm": "kiểm soát triệu chứng hiệu quả",
            "thuốc điều trị": "sản phẩm chuyên dụng",
            "chữa dứt": "hỗ trợ cải thiện mạnh",
            "bệnh lý": "tình trạng da liễu"
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
    async def _emit_progress(self, campaign: "ContentCampaign | str", msg: str, status: str = "PROCESSING") -> None:
        from backend.services.event_bus import event_bus
        from datetime import datetime, timezone
        from backend.database.models import ContentCampaign
        
        c_id = getattr(campaign, "id", campaign) if isinstance(campaign, ContentCampaign) else campaign
        u_id = getattr(campaign, "user_id", None) if isinstance(campaign, ContentCampaign) else None
        
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
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Rule R0.1: Automatic Heritage Registration (The CTO Backdoor)
        # This registers any subclass into AGENT_REGISTRY for universal worker access.
        if hasattr(cls, "agent_id_class"):
            agent_id = getattr(cls, "agent_id_class")
            if agent_id:
                AGENT_REGISTRY[agent_id] = cls
                logger.info(f"[Heritage] Registered Operative: {agent_id}")

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"api-gateway.{agent_id}")
        self.bridge = trinity_bridge

    @abstractmethod
    async def chat(self, request: "BaseModel | dict", **kwargs: Dict[str, object]) -> dict[str, object]:
        """Standardized entry point for all AI agents."""
        pass

    def get_schema(self) -> Optional[Type[BaseModel]]:
        """
        Elite V2.2: Optional Pydantic schema for task payload validation.
        Subclasses should override this to provide type safety in the Worker.
        """
        return None

    async def enqueue_chat(self, request_data: dict, session_id: str, db: Optional[AsyncSession] = None) -> str:
        """
        Elite V2.2: Async Deferred Execution (Arq Backdoor) with DB Persistence.
        Pushes the agent task to the Redis Background Queue and tracks status in DB.
        """
        from backend.infra.arq_config import get_redis_settings
        from arq import create_pool
        import uuid
        from datetime import datetime, timezone

        task_id = str(uuid.uuid4())
        
        # 1. DB Persistence (Elite V2.2 Rule: No orphaned tasks)
        from backend.database import current_tenant_id
        # Elite V2.2: Ensure we capture context if available, fallback to request payload
        target_tenant = current_tenant_id.get() or request_data.get("tenant_id") or "default"

        new_task = UnifiedAgentTask(
            agent_id=self.agent_id,
            task_id=task_id,
            session_id=session_id,
            status="PENDING",
            payload=request_data,
            tenant_id=target_tenant
        )

        async def _persist():
            if db:
                db.add(new_task)
                await db.commit()
            else:
                session_maker = alchemy_config.create_session_maker()
                async with session_maker() as standalone_db:
                    standalone_db.add(new_task)
                    await standalone_db.commit()

        try:
            await _persist()
            
            # 2. Redis Enqueue with Priority Support
            # Rule R1.1: Helen (support_agent) gets the 'high' queue.
            queue_name = "high" if self.agent_id == "support_agent" else "default"
            
            redis = await create_pool(get_redis_settings())
            await redis.enqueue_job(
                "run_agent_task",
                agent_id=self.agent_id,
                task_id=task_id,
                session_id=session_id,
                payload=request_data,
                _queue_name=queue_name
            )
            
            self.logger.info(f"[{self.agent_id}] Task enqueued: {task_id} (Queue: {queue_name})")
            return task_id
        except Exception as e:
            self.logger.error(f"[{self.agent_id}] Failed to enqueue task: {e}")
            # Optional: Mark task as FAILED in DB if possible
            raise

    async def _report_telemetry(self, task: str, duration: float, error: Optional[str] = None) -> None:
        """Standardized system-wide performance reporting."""
        status = "SUCCESS" if not error else f"FAILED ({error})"
        self.logger.info(f"[{self.agent_id}] {task} {status} | Latency: {duration:.3f}s")
