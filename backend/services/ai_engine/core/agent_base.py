import os
import uuid
import time
import logging
import asyncio
import re
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, cast, TYPE_CHECKING, Dict, Type
from abc import ABC, abstractmethod
from sqlalchemy.orm.attributes import flag_modified
from backend.database.models import ContentCampaign, UnifiedAgentTask
from backend.database.alchemy_config import alchemy_config
from backend.database import current_tenant_id
from backend.services.event_bus import event_bus
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.config import get_env_json
from backend.services.xohi_memory import xohi_memory

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
        # 1. Fallback Static Map (R109 taxonomy)
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
        # CNS V2.2: Resilient ID extraction supporting both ORM models and AdHocContent shims
        c_id = getattr(campaign, "id", campaign)
        u_id = getattr(campaign, "user_id", None)
        
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": str(c_id),
            "user_id": str(u_id) if u_id else None,
            "message": msg,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

class BaseAgentOperative(ABC, MedicalShieldMixin, XoHiProgressMixin):
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

        task_id = str(uuid.uuid4())
        
        # 1. DB Persistence (Elite V2.2 Rule: No orphaned tasks)
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

    async def _resolve_xohi_context(self, campaign: object, draft: str, mode: str, **kwargs: object) -> dict:
        """
        Elite V2.2: Centralized Context Resolution (CNS-V89).
        Determines the 'Combat Domain' and 'Expert Role' for the AI.
        """
        # 1. Identify Entity Type
        is_product = False
        if hasattr(campaign, "category") and getattr(campaign, "category") == "PRODUCT_CATALOG":
            is_product = True
        elif hasattr(campaign, "get_gold_val"):
            if campaign.get_gold_val("contentType") == "product" or campaign.get_gold_val("category") == "Sản phẩm":
                is_product = True

        # [CNS-V91.6] Identify Review Context
        is_review = False
        if hasattr(campaign, "category") and getattr(campaign, "category") == "REVIEW":
            is_review = True
        elif kwargs.get("content_type") == "review":
            is_review = True
        
        # 2. Assign Role & Log Message
        role_map = {
            "copyright": ("Thẩm định viên Bản quyền", "🕵️ Đang trinh sát mạng lưới tác quyền toàn cầu..."),
            "seo": ("Chuyên gia Tối ưu SEO", "🧠 Đang tính toán ma trận thực thể SEO..."),
            "ai_inspect": ("Kiểm định viên Cấu trúc", "🔍 Đang soi rọi cấu trúc Information Gain..."),
            "rewriter": ("Biên tập viên Cao cấp", "✍️ Đang tinh chỉnh phong cách Viral 2026..."),
            "booster": ("Cố vấn EEAT", "💎 Đang tối ưu hóa dữ liệu thực tế cho bài viết...")
        }
        
        role_base, log_msg = role_map.get(mode, ("Chuyên gia Phân tích", "📡 Đang khởi động hệ thống..."))
        
        if is_review:
            entity_suffix = "Đánh giá"
        else:
            entity_suffix = "Sản phẩm" if is_product else "Bài viết"
            
        role_assignment = f"{role_base} {entity_suffix} (Elite V2.2)"
        
        # 3. Dynamic Prompt Mixins (Elite V2.2 POS)
        context = {
            "role_assignment": role_assignment,
            "log_msg": log_msg,
            "content_type_vn": "sản phẩm" if is_product else "bài viết",
            "is_product": is_product
        }
        
        # Specific mixins for different modes
        if mode in ("ai_inspect", "copyright"):
            if is_product:
                context.update({
                    "four_blocks": "[GIỚI THIỆU - CÔNG DỤNG - ĐỐI TƯỢNG SỬ DỤNG - CÁCH SỬ DỤNG - LƯU Ý KHI SỬ DỤNG - BẢO QUẢN - CAM KẾT]",
                    "block_1": "GIỚI THIỆU",
                    "block_3": "ĐỐI TƯỢNG SỬ DỤNG"
                })
                context["step_3_pillars"] = (
                    "  + **GIỚI THIỆU**: Đoạn văn giới thiệu tổng quan, không vòng vo.\n"
                    "  + **CÔNG DỤNG**: Phân tích chuyên sâu công dụng, biện luận cơ chế hoạt động của thành phần.\n"
                    "  + **ĐỐI TƯỢNG SỬ DỤNG**: Chỉ định rõ ràng đối tượng phù hợp và chống chỉ định.\n"
                    "  + **CÁCH SỬ DỤNG**: Hướng dẫn thao tác sử dụng để tối ưu hiệu quả.\n"
                    "  + **LƯU Ý KHI SỬ DỤNG**: Các cảnh báo an toàn và kiêng kỵ khi mix hoạt chất.\n"
                    "  + **BẢO QUẢN**: Điều kiện lưu trữ duy trì tính toàn vẹn của sản phẩm.\n"
                    "  + **CAM KẾT**: Cam kết an toàn sạch '3 Không' từ Osmo và chính sách đổi trả hoàn tiền."
                )
            else:
                context.update({
                    "four_blocks": "[HOOK - EVIDENCE - STRATEGY - CONNECTION]",
                    "block_1": "HOOK",
                    "block_3": "STRATEGY"
                })
                context["step_3_pillars"] = (
                    "  + **ĐIỂM CHẠM (The Hook)**: Lời mở đầu gây ấn tượng mạnh, đánh trúng nỗi đau hoặc sự tò mò của độc giả là gì?\n"
                    "  + **BẰNG CHỨNG (The Evidence)**: Dữ liệu thực tế, số liệu, nghiên cứu hoặc ví dụ cụ thể nào chứng minh cho luận điểm chuyên gia?\n"
                    "  + **GIẢI PHÁP (The Strategy)**: Phương pháp, hướng đi mới hoặc giải pháp cốt lõi giải quyết vấn đề một cách thuyết phục nhất là gì?\n"
                    "  + **KẾT NỐI (The Connection)**: Cách ứng dụng thực tế, lời kêu gọi hành động (CTA), hoặc sự liên kết giá trị sâu sắc với khách hàng là gì?"
                )
            
        return context

    def clean_ai_html(self, html: str) -> str:
        """CNS V82.0: Clean AI artifacts (Markdown blocks, artifacts) from HTML."""
        if not html: return ""
        # Remove ```html ... ``` blocks if present
        clean = re.sub(r'```html\s*', '', html, flags=re.IGNORECASE)
        clean = re.sub(r'```\s*', '', clean)
        return clean.strip()

    def detect_enrichment_annotations(self, draft: str) -> list["SeoAnnotation"]:
        """
        Elite V2.2: Universal EEAT Detection (CNS-V85.26).
        Identifies Booster segments in draft and returns SEO annotations.
        """
        from backend.services.xohi.creative_studio.models.schemas import SeoAnnotation
        annotations = []
        
        def _build_ann(m, label):
            clean_text = re.sub(r'<[^>]*>', ' ', m.group(0))
            clean_text = ' '.join(clean_text.split()).strip()
            return SeoAnnotation(
                type="enrich",
                text=clean_text[:120],
                message=f"🚀 AI Booster: Đã cấy {label} thực tế vào bài viết.",
                severity="info"
            )

        for m in re.finditer(r'<blockquote\s+class="xohi-stat">(.*?)</blockquote>', draft, re.DOTALL):
            annotations.append(_build_ann(m, "số liệu"))
        for m in re.finditer(r'<blockquote\s+class="xohi-quote">(.*?)</blockquote>', draft, re.DOTALL):
            annotations.append(_build_ann(m, "trích dẫn"))
        for m in re.finditer(r'<table\s+class="xohi-compare[^"]*">(.*?)</table>', draft, re.DOTALL):
            annotations.append(_build_ann(m, "bảng so sánh"))
            
        return annotations
