import re
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Union, Optional, cast
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.xohi.creative_studio.models.schemas import (
    AiReadyReport, AutoFixResponse, BulkFixResponse, BulkFixRequest,
    GoldMetadata, AiAnnotation, AtomicFixResponse, SurgicalSnippetFix
)
from backend.services.xohi.creative_studio.utils.stitcher import surgical_stitch
from .ai_inspector_prompts import GEO_ANALYSIS_PROMPT, SURGEON_PROMPT, ATOMIC_SURGEON_PROMPT

logger = logging.getLogger("api-gateway")

class AiInspector:
    """
    VIRAL EDGE Algorithm — AI-powered SEO & AI-Ready Auditor.
    Complying with Martial Law (<300 lines) by externalizing prompts.
    """
    def __init__(self):
        self._agent = Agent(output_type=AiReadyReport, system_prompt=GEO_ANALYSIS_PROMPT, retries=3)
        self._surgeon_agent = Agent(output_type=AutoFixResponse, system_prompt=SURGEON_PROMPT, retries=2)
        self._atomic_surgeon_agent = Agent(output_type=AtomicFixResponse, system_prompt=ATOMIC_SURGEON_PROMPT, retries=2)

    async def _emit_log(self, campaign: ContentCampaign, msg: str):
        """Emit progress event to the system bus."""
        from backend.services.event_bus import event_bus
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": str(campaign.id),
            "user_id": str(campaign.user_id),
            "message": msg,
            "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def analyze(self, campaign: ContentCampaign, force: bool = False) -> AiReadyReport:
        logs = ["🚀 Khởi động Neural AI-Ready Engine (XoHi 2026)..."]
        await self._emit_log(campaign, logs[-1])
        
        draft = campaign.draft_content or ""
        if not draft: return AiReadyReport(geo_score=0, summary="Thiếu dữ liệu.", logs=logs)
        
        logs.append("🧠 Đang phân tích NLP Entity Density & Information Gain...")
        await self._emit_log(campaign, logs[-1])
        try:
            res = await trinity_bridge.run(self._agent, draft[:12000], role="pro") # Use Pro for high-IQ analysis
            raw = res.data if hasattr(res, "data") else res.output
            raw.logs = logs
            return raw
        except Exception as e:
            logger.error(f"[AiInspector] Analysis failed: {e}")
            return AiReadyReport(geo_score=75, summary="AI bận, thử lại sau.", logs=logs)

    async def auto_fix(self, campaign: ContentCampaign, annotation: AiAnnotation) -> AutoFixResponse:
        content = campaign.draft_content or ""
        snippet, issue = annotation.text, annotation.message
        prompt = f"[BÀI VIẾT]\n{content[:5000]}\n\n[ĐOẠN LỖI]\n{snippet}\n\n[LÝ DO]\n{issue}"
        try:
            res = await trinity_bridge.run(self._surgeon_agent, prompt, role="fast")
            return res.data if hasattr(res, "data") else res.output
        except Exception as e:
            logger.error(f"[AiInspector] Auto-fix failed: {e}")
            return AutoFixResponse(old_text=snippet, new_text=snippet)

    async def atomic_bulk_fix(self, campaign: ContentCampaign, req: BulkFixRequest) -> BulkFixResponse:
        logs = ["🚀 Khởi động Neural Surgical Engine (Elite V2.2)..."]
        await self._emit_log(campaign, logs[-1])
        
        draft = await noise_cleaner.clean(campaign.draft_content or "", mode="light", strip_html=False)
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

        logs.append(f"🧠 Đang xử lý {len(valid_items)} điểm yếu qua AI Surgeon...")
        await self._emit_log(campaign, logs[-1])
        prompt = f"{ATOMIC_SURGEON_PROMPT}\n\n[CẦN SỬA]\n{snippet_list}"
        
        try:
            res = await trinity_bridge.run(self._atomic_surgeon_agent, prompt, role="fast", timeout=120.0)
            raw = res.data if hasattr(res, "data") else res.output
            final_content = draft
            replacements_made = 0
            replacements_log = []
            if hasattr(raw, "replacements"):
                for fix in sorted(raw.replacements, key=lambda x: len(next((v["old_text"] for v in valid_items if v["id"] == x.id), "")), reverse=True):
                    orig = next((v for v in valid_items if v["id"] == fix.id), None)
                    if orig and fix.new_text:
                        old, new = orig["old_text"], await noise_cleaner.clean(fix.new_text, mode="light", strip_html=False)
                        new_c = surgical_stitch(final_content, old, new, label="AiInspector")
                        if new_c != final_content:
                            final_content, replacements_made = new_c, replacements_made + 1
                            replacements_log.append({"old_text": old, "new_text": new})
                            logs.append(f"✅ Đã phẫu thuật: \"{old[:30]}...\"")
                            await self._emit_log(campaign, logs[-1])
            logs.append(f"🏅 Hoàn tất! Đã tối ưu {replacements_made} phân đoạn.")
            await self._emit_log(campaign, logs[-1])
            return BulkFixResponse(new_content=final_content, logs=logs, replacements=replacements_log)
        except Exception as e:
            logger.error(f"[AiInspector] Bulk fix failed: {e}")
            return BulkFixResponse(new_content=draft, logs=logs)
