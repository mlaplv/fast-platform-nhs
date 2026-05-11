import re
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple, cast, Set
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.xohi.creative_studio.models.schemas import (
    BulkFixRequest, BulkFixResponse, AtomicFixResponse, SnippetRefinement
)
from backend.services.ai_engine.core.agent_base import XoHiProgressMixin
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner
from backend.utils.text import normalize_vn
from backend.services.xohi.creative_studio.utils.stitcher import refinement_stitch
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.shields.service import shield_service

logger = logging.getLogger("api-gateway")

RE_DIGIT = re.compile(r'\d+')

class PlagiarismRefiner(XoHiProgressMixin):
    """
    Handles deterministic deduplication and AI-powered surgical fixes for Copyright.
    Elite V2.2: Context-Aware with Neural Prompt Orchestration (NPO).
    """
    def __init__(self):
        self._atomic_surgeon_agent = Agent(
            output_type=AtomicFixResponse,
            retries=2
        )

    def clean_ai_html(self, html: str) -> str:
        """CNS V82.0: Clean AI artifacts (Markdown blocks) from HTML output."""
        if not html:
            return ""
        clean = re.sub(r'```html\s*', '', html, flags=re.IGNORECASE)
        clean = re.sub(r'```\s*', '', clean)
        return clean.strip()


    async def _emit_log(self, campaign: ContentCampaign, msg: str) -> None:
        """Helper to emit logs to the SSE stream."""
        await self._emit_progress(campaign, msg)

    def _split_into_paragraphs(self, html_or_text: str) -> List[str]:
        if not html_or_text: return []
        p = re.sub(r'</(p|div|h[1-6]|li|blockquote|table|figure)>', r'</\1>\n\n', html_or_text, flags=re.IGNORECASE)
        return [it.strip() for it in re.split(r'\n\n+', p) if it.strip()]

    def _tokenize(self, text: str) -> set[str]:
        norm = normalize_vn(text)
        norm = RE_DIGIT.sub('', norm)
        return {w for w in norm.split() if len(w) >= 2}

    def _jaccard(self, a: set[str], b: set[str]) -> float:
        if not a and not b: return 1.0
        if not a or not b: return 0.0
        intersect = len(a & b)
        return intersect / (len(a) + len(b) - intersect)

    async def bulk_fix(self, campaign: ContentCampaign, req: BulkFixRequest) -> BulkFixResponse:
        self.current_step = 0
        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        logs = [f"🚀 [{now_str}] [REFINER] Initializing Neural Refinement Engine (Elite V2.2)..."]
        await self._emit_log(campaign, logs[-1])
        logger.warning(f"🚀 [PlagiarismRefiner] Initializing [REFINER] Phase 0: Patch Preparation...")
        
        draft = campaign.draft_content or ""
        cleaned_draft = draft
        
        annots = req.annotations if isinstance(req.annotations, list) else []
        all_annots = [a for a in annots if (a.get("text") or a.get("reason")) and len(str(a.get("text",""))) > 5]
        
        valid_items = []
        snippet_list = ""
        for i, a in enumerate(all_annots[:40]):
            txt = str(a.get("text") or a.get("reason") or "").strip()
            reason = str(a.get("message") or a.get("reason") or "Cần tối ưu nội dung").strip()
            if len(txt) < 5: continue
            snippet_list += f"\n[ID {i+1}]:\n- Cần sửa: \"{txt}\"\n- Lỗi cần khắc phục: {reason}\n"
            valid_items.append({"id": i+1, "old_text": txt})

        if not valid_items:
            return BulkFixResponse(new_content=cleaned_draft, logs=logs)

        logs.append(f"🔍 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [SCAN] Ingesting {len(valid_items)} violation points into AI Refiner...")
        await self._emit_log(campaign, logs[-1])
        self.current_step = 1
        logger.warning(f"🔍 [PlagiarismRefiner] Phase 1: [SCAN] Context Ingestion complete.")
        
        self.current_step = 2
        logger.warning(f"🧠 [PlagiarismRefiner] Phase 2: [BRAIN] Refinement processing pending...")
        
        gold = dict(campaign.gold_metadata or {})
        cache = dict(gold.get("analysis_cache", {}))
        copyright_cache = cache.get("copyright", {}).get("data", {})
        similar_sources = copyright_cache.get("similar_sources", [])
        
        source_context = ""
        if similar_sources:
            source_context = "\n[NGUỒN ĐỐI CHIẾU CẦN TRÁNH]\n" + "\n".join(similar_sources[:3])
        
        shield = shield_service.get_shield_component(seed=campaign.id)
        composer.register_component(shield)
        
        # ELITE V2.2: Use extra_components to maintain thread-safety
        system_prompt = composer.compose("copyright_refiner", extra_components=[shield.id])

        bulk_prompt = f"{source_context}\n\n[DANH SÁCH CẦN SỬA]\n{snippet_list}"
        
        try:
            res = await trinity_bridge.run(self._atomic_surgeon_agent, bulk_prompt, system_prompt=system_prompt, role="fast", timeout=120.0)
            raw_data = res
            final_content = cleaned_draft
            replacements_made = 0
            replacements_log = []
            
            if hasattr(raw_data, 'data') and not hasattr(raw_data, 'replacements'):
                raw_data = raw_data.data

            if hasattr(raw_data, "replacements"):
                logs.append(f"💉 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [PATCH] AI surgery plan received. Applying {len(raw_data.replacements)} patches...")
                await self._emit_log(campaign, logs[-1])
                
                sorted_fixes = sorted(raw_data.replacements, key=lambda x: len(next((v["old_text"] for v in valid_items if v["id"] == x.id), "")), reverse=True)
                for fix in sorted_fixes:
                    orig_item = next((v for v in valid_items if v["id"] == fix.id), None)
                    if orig_item and fix.new_text:
                        old_txt = orig_item["old_text"]
                        new_txt = await noise_cleaner.clean(fix.new_text, mode="light", strip_html=False)
                        new_content = refinement_stitch(final_content, old_txt, new_txt, label="PlagiarismRefiner")
                        if new_content != final_content:
                            final_content = new_content
                            replacements_made += 1
                            replacements_log.append({"old_text": old_txt, "new_text": new_txt})
                            logs.append(f"✅ [REFINER] Successfully patched: \"{old_txt[:40]}...\"")
                            await self._emit_log(campaign, logs[-1])
            
            self.current_step = 3
            logs.append(f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [QUANTUM] Bulk fix complete. Successfully optimized {replacements_made}/{len(valid_items)} segments. ĐÃ XỬ LÝ XONG")
            await self._emit_log(campaign, logs[-1])
            logger.warning(f"✅ [PlagiarismRefiner] [QUANTUM] Bulk fix complete.")
            final_content = self.clean_ai_html(final_content)
            return BulkFixResponse(new_content=final_content, logs=logs, replacements=replacements_log)
        except Exception as e:
            logger.error(f"[PlagiarismRefiner] AI Bulk Fix failed: {e}")
            return BulkFixResponse(new_content=cleaned_draft, logs=logs)
