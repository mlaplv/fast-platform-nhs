import re
import asyncio
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Union, Optional, cast, Type
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import ContentCampaign
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.database.repositories import ContentCampaignRepository
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.xohi.creative_studio.models.schemas import (
    AiReadyReport, AutoFixResponse, BulkFixResponse, BulkFixRequest,
    GoldMetadata, AiAnnotation, AtomicFixResponse, SnippetRefinement
)
from backend.services.xohi.creative_studio.utils.stitcher import refinement_stitch
from backend.utils.text import extract_readable_text, is_json

from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.shields.service import shield_service

logger = logging.getLogger("api-gateway")

class AiInspectorTaskRequest(BaseModel):
    """Worker task payload for AiInspector."""
    campaign_id: str
    force: bool = False

class AutoFixRequest(BaseModel):
    """Request for auto-fix a single annotation."""
    text: str = ""
    message: str = ""

class AiInspector(BaseAgentOperative):
    """
    VIRAL EDGE Algorithm — AI-powered SEO & AI-Ready Auditor.
    Elite V2.2: Context-Aware with Neural Prompt Orchestration (NPO).
    """
    agent_id_class = "ai_inspector"

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="ai_inspector")
        self._agent = Agent(output_type=AiReadyReport, retries=3)
        self._refiner_agent = Agent(output_type=AutoFixResponse, retries=2)
        self._atomic_refiner_agent = Agent(output_type=AtomicFixResponse, retries=2)

    async def _emit_log(self, campaign: ContentCampaign, msg: str) -> None:
        """Backward-compat alias → delegates to Heritage _emit_progress."""
        await self._emit_progress(campaign, msg)

    async def chat(self, request: object, **kwargs: object) -> Union[AiReadyReport, dict]:
        """Standardized Heritage Entry (V2.2). Maps to self.analyze."""
        if isinstance(request, ContentCampaign):
            return await self.analyze(request, force=bool(kwargs.get("force", False)))
        return await self.analyze(cast(ContentCampaign, request), **kwargs)  # type: ignore

    def get_schema(self) -> Optional[Type[BaseModel]]:
        return AiInspectorTaskRequest

    async def process_brain_logic(self, request: AiInspectorTaskRequest, db: AsyncSession) -> AiReadyReport:
        """Elite V2.2: Async worker execution for AI-Ready analysis."""
        repo = ContentCampaignRepository(session=db)
        campaign = await repo.get(request.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {request.campaign_id} not found")

        result = await self.analyze(campaign, force=request.force)

        # Persist to gold_metadata
        gold = dict(campaign.gold_metadata or {})
        cache = dict(gold.get("analysis_cache", {}))
        metrics = dict(gold.get("analysis_metrics", {}))
        content_hash = hashlib.sha256((campaign.draft_content or "").encode('utf-8')).hexdigest()
        cache["ai_inspect"] = {"hash": content_hash, "data": result.model_dump(), "at": datetime.now(timezone.utc).isoformat()}
        metrics["geo_score"] = result.geo_score
        gold["analysis_cache"], gold["analysis_metrics"] = cache, metrics
        campaign.gold_metadata = gold
        flag_modified(campaign, "gold_metadata")
        await repo.update(campaign)
        return result


    async def analyze(self, campaign: ContentCampaign, force: bool = False) -> AiReadyReport:
        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        self.current_step = 0
        logs = [f"🚀 [{now_str}] [GEO] Initializing Neural AI-Ready Engine (XoHi 2026)..."]
        await self._emit_log(campaign, logs[-1])
        logger.warning(f"🚀 [AiInspector] Initializing [GEO] Structural Scan Phase...")
        
        original_draft = campaign.draft_content or ""
        draft = extract_readable_text(original_draft)
        word_count = len(draft.split())
        logs.append(f"🔍 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [GEO] Structural Scan: {word_count} words. Analyzing NLP Entity Density & Information Gain...")
        await self._emit_log(campaign, logs[-1])
        self.current_step = 1
        logger.warning(f"🔍 [AiInspector] Running [REFINER] NLP Entity Density analysis...")
        
        # [CNS-V89] Resolve Context via Centralized Intelligence
        context = await self._resolve_xohi_context(campaign, draft, "ai_inspect")
        await self._emit_log(campaign, context["log_msg"])
        
        logs.append(f"🛡️ [ROLE] Đã xác nhận phân vai tác chiến: {context['role_assignment']}")
        await self._emit_log(campaign, logs[-1])

        logs.append(f"🛡️ [SHIELD] Đã kích hoạt SGE Shield V2.1 (Anti-AI Footprint)")
        await self._emit_log(campaign, logs[-1])

        is_adhoc = str(getattr(campaign, "id", "adhoc")) == "adhoc"
        logs.append(f"🛡️ [SAFETY] Chế độ Ad-hoc Safety: {'ACTIVE' if is_adhoc else 'CAMPAIGN_MODE'}")
        await self._emit_log(campaign, logs[-1])
        
        shield = shield_service.get_shield_component(seed=str(getattr(campaign, "id", "adhoc")))
        composer.register_component(shield)
        
        # ELITE V2.2: Use extra_components to maintain thread-safety
        system_prompt = composer.compose("inspector_analysis", context=context, extra_components=[shield.id])
        self.current_step = 2
        logger.warning(f"🧠 [AiInspector] Entering [JUDGE] AI Readiness Phase (Brain response pending)...")
        
        try:
            res = await trinity_bridge.run(self._agent, draft[:50000], system_prompt=system_prompt, role="pro", safety_none=True) 
            raw = res
            if hasattr(raw, 'data') and not hasattr(raw, 'geo_score'):
                raw = raw.data
                
            self.current_step = 3
            logs.append(f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [QUANTUM] Kiểm tra cấu trúc hoàn tất! Phát hiện {len(getattr(raw, 'ai_annotations', []))} điểm tối ưu hóa. ĐÃ XỬ LÝ XONG")
            await self._emit_log(campaign, logs[-1])
            logger.warning(f"✅ [AiInspector] [QUANTUM] Completed. Score: {raw.geo_score}")
            
            # Elite V2.2: Prepend report timestamp to summary for traceability (UTC+7)
            report_time = (datetime.now(timezone.utc) + timedelta(hours=7)).strftime('%H:%M:%S %d/%m/%Y')
            time_badge = f"> [!IMPORTANT]\n> **THỜI GIAN LẬP BÁO CÁO:** {report_time}\n\n"
            
            if hasattr(raw, 'summary'):
                raw.summary = time_badge + (raw.summary or "")
            
            raw.logs = logs
            return raw
        except Exception as e:
            logger.error(f"[AiInspector] Analysis failed: {e}")
            return AiReadyReport(geo_score=75, summary="AI bận, thử lại sau.", logs=logs)

    async def auto_fix(self, campaign: ContentCampaign, annotation: AiAnnotation) -> AutoFixResponse:
        content = extract_readable_text(campaign.draft_content or "")
        snippet, issue = annotation.text, annotation.message
        
        shield = shield_service.get_shield_component(seed=campaign.id)
        composer.register_component(shield)
        
        system_prompt = composer.compose("inspector_refiner", extra_components=[shield.id])
        
        prompt = f"[BÀI VIẾT]\n{content[:5000]}\n\n[ĐOẠN LỖI]\n{snippet}\n\n[LÝ DO]\n{issue}"
        try:
            res = await trinity_bridge.run(self._refiner_agent, prompt, system_prompt=system_prompt, role="fast", safety_none=True)
            raw = res
            if hasattr(raw, 'data') and not hasattr(raw, 'new_text'):
                raw = raw.data
            return raw
        except Exception as e:
            logger.error(f"[AiInspector] Auto-fix failed: {e}")
            return AutoFixResponse(old_text=snippet, new_text=snippet)

    async def bulk_fix(self, campaign: ContentCampaign, req: BulkFixRequest) -> BulkFixResponse:
        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        self.current_step = 0
        logs = [f"🚀 [{now_str}] [REFINER] Initializing Neural AI-Ready Refiner (Elite V2.2)..."]
        await self._emit_log(campaign, logs[-1])
        logger.warning(f"🚀 [AiInspector] Initializing [REFINER] Bulk Fix Phase 0...")
        
        original_draft = campaign.draft_content or ""
        if not is_json(original_draft):
            draft = await noise_cleaner.clean(original_draft, mode="light", strip_html=False)
        else:
            draft = original_draft
        annots = req.annotations if isinstance(req.annotations, list) else []
        valid_items = []
        snippet_list = ""

        for i, a in enumerate(annots[:40]):
            txt_raw = str(a.get('text', '')).strip()
            if len(txt_raw) < 5: continue
            txt = await noise_cleaner.clean(txt_raw, mode="light", strip_html=False)
            snippet_list += f"\n[ID {i+1}]:\n- Cần sửa: \"{txt}\"\n- Lỗi: {a.get('message','')}\n"
            valid_items.append({"id": i+1, "old_text": txt})

        if not valid_items: return BulkFixResponse(new_content=draft, logs=logs)

        logs.append(f"🔍 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [SCAN] Ingesting {len(valid_items)} structural weaknesses into AI Refiner...")
        await self._emit_log(campaign, logs[-1])
        self.current_step = 1
        logger.warning(f"🔍 [AiInspector] Phase 1: [SCAN] Structural analysis start.")
        
        self.current_step = 2
        logger.warning(f"🧠 [AiInspector] Phase 2: [BRAIN] AI Refinement pending...")
        
        # ELITE V2.2: Identify content type (Military-grade safety)
        is_product = getattr(campaign, "category", "") == "PRODUCT_CATALOG" or \
                     (hasattr(campaign, "get_gold_val") and (campaign.get_gold_val("contentType") == "product" or campaign.get_gold_val("category") == "Sản phẩm"))
        
        context = {
            "four_blocks": "[USP - SCIENCE - METHOD - TRUST]" if is_product else "[HOOK - EVIDENCE - STRATEGY - CONNECTION]",
            "content_type_vn": "sản phẩm" if is_product else "bài viết",
            "block_1": "USP" if is_product else "HOOK",
            "block_3": "METHOD" if is_product else "STRATEGY",
            "role_assignment": "Chuyên gia Tinh chỉnh Viral Sản phẩm (Elite V2.2)" if is_product else "Chuyên gia Tinh chỉnh Viral Bài viết (Elite V2.2)"
        }
        
        shield = shield_service.get_shield_component(seed=str(getattr(campaign, "id", "adhoc")))
        composer.register_component(shield)
        
        # ELITE V2.2: Use extra_components to maintain thread-safety
        system_prompt = composer.compose("inspector_refiner", context=context, extra_components=[shield.id])

        prompt = f"[CẦN SỬA]\n{snippet_list}"
        
        try:
            res = await trinity_bridge.run(self._atomic_refiner_agent, prompt, system_prompt=system_prompt, role="fast", timeout=120.0, safety_none=True)
            raw = res
            if hasattr(raw, 'data') and not hasattr(raw, 'replacements'):
                raw = raw.data
                
            final_content = draft
            replacements_made = 0
            replacements_log = []
            if hasattr(raw, "replacements"):
                for fix in sorted(raw.replacements, key=lambda x: len(next((v["old_text"] for v in valid_items if v["id"] == x.id), "")), reverse=True):
                    orig = next((v for v in valid_items if v["id"] == fix.id), None)
                    if orig and fix.new_text:
                        old, new = orig["old_text"], await noise_cleaner.clean(fix.new_text, mode="light", strip_html=False)
                        new_c = refinement_stitch(final_content, old, new, label="AiInspector")
                        if new_c != final_content:
                            final_content, replacements_made = new_c, replacements_made + 1
                            replacements_log.append({"old_text": old, "new_text": new})
                            logs.append(f"✅ [REFINER] Optimized: \"{old[:40]}...\"")
                            await self._emit_log(campaign, logs[-1])
            self.current_step = 3
            logs.append(f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [QUANTUM] Tinh chỉnh cấu trúc hoàn tất! Đã tối ưu {replacements_made}/{len(valid_items)} phân đoạn. ĐÃ XỬ LÝ XONG")
            await self._emit_log(campaign, logs[-1])
            logger.warning(f"✅ [AiInspector] [QUANTUM] Bulk fix complete.")
            final_content = self.clean_ai_html(final_content)
            return BulkFixResponse(new_content=final_content, logs=logs, replacements=replacements_log)
        except Exception as e:
            logger.error(f"[AiInspector] Bulk fix failed: {e}")
            return BulkFixResponse(new_content=draft, logs=logs)
