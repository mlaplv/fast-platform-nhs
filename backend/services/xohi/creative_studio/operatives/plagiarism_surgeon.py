import re
import asyncio
import logging
from typing import List, Dict, Optional, Tuple, cast, Set
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.xohi.creative_studio.models.schemas import (
    BulkFixRequest, BulkFixResponse, AtomicFixResponse, SurgicalSnippetFix
)
from backend.services.ai_engine.core.agent_base import XoHiProgressMixin
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner
from backend.utils.text import normalize_vn
from backend.services.xohi.creative_studio.utils.stitcher import surgical_stitch
from .plagiarism_prompts import PLAGIARISM_SURGEON_PROMPT

logger = logging.getLogger("api-gateway")

RE_DIGIT = re.compile(r'\d+')

class PlagiarismSurgeon(XoHiProgressMixin):
    """
    Handles deterministic deduplication and AI-powered surgical fixes for Copyright.
    Separated from PlagiarismCop to comply with Martial Law line limits (<300 lines).
    """
    def __init__(self):
        self._atomic_surgeon_agent = Agent(
            system_prompt=PLAGIARISM_SURGEON_PROMPT,
            output_type=AtomicFixResponse,
            retries=2
        )

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
        logs = ["[SURGEON] Initializing Neural Surgical Engine (Elite V2.2)..."]
        await self._emit_log(campaign, logs[-1])
        
        # R110: Use raw draft content to ensure surgical snippets (annotations) match perfectly.
        draft = campaign.draft_content or ""

        # R110: Simplified Bulk Fix. We avoid aggressive dedup here to ensure 
        # surgical replacements match the editor's current structure.
        cleaned_draft = draft
        
        # AI Surgeon for external plagiarism
        annots = req.annotations if isinstance(req.annotations, list) else []
        all_annots = [a for a in annots if (a.get("text") or a.get("reason")) and len(str(a.get("text",""))) > 5]
        
        valid_items = []
        snippet_list = ""
        for i, a in enumerate(all_annots[:40]):
            txt = str(a.get("text") or a.get("reason") or "").strip()
            if len(txt) < 5: continue
            snippet_list += f"\n[ID {i+1}]:\n- Cần sửa: \"{txt}\"\n"
            valid_items.append({"id": i+1, "old_text": txt})

        if not valid_items:
            return BulkFixResponse(new_content=cleaned_draft, logs=logs)

        logs.append(f"[SCAN] Ingesting {len(valid_items)} violation points into AI Surgeon...")
        await self._emit_log(campaign, logs[-1])
        
        bulk_prompt = f"{PLAGIARISM_SURGEON_PROMPT}\n\n[DANH SÁCH CẦN SỬA]\n{snippet_list}"
        
        try:
            res = await trinity_bridge.run(self._atomic_surgeon_agent, bulk_prompt, role="fast", timeout=120.0)
            raw_data = res
            final_content = cleaned_draft
            replacements_made = 0
            replacements_log = []
            
            # Use data attribute if trinity_bridge returned the raw AgentRunResult
            if hasattr(raw_data, 'data') and not hasattr(raw_data, 'replacements'):
                raw_data = raw_data.data

            if hasattr(raw_data, "replacements"):
                logs.append(f"[PATCH] AI surgery plan received. Applying {len(raw_data.replacements)} patches...")
                await self._emit_log(campaign, logs[-1])
                
                # Sort by length descending to avoid nested replacement issues
                sorted_fixes = sorted(raw_data.replacements, key=lambda x: len(next((v["old_text"] for v in valid_items if v["id"] == x.id), "")), reverse=True)
                for fix in sorted_fixes:
                    orig_item = next((v for v in valid_items if v["id"] == fix.id), None)
                    if orig_item and fix.new_text:
                        old_txt = orig_item["old_text"]
                        new_txt = await noise_cleaner.clean(fix.new_text, mode="light", strip_html=False)
                        new_content = surgical_stitch(final_content, old_txt, new_txt, label="PlagiarismSurgeon")
                        if new_content != final_content:
                            final_content = new_content
                            replacements_made += 1
                            replacements_log.append({"old_text": old_txt, "new_text": new_txt})
                            logs.append(f"✅ [SURGEON] Successfully patched: \"{old_txt[:40]}...\"")
                            await self._emit_log(campaign, logs[-1])
            
            logs.append(f"[QUANTUM] Bulk fix complete. Successfully optimized {replacements_made}/{len(valid_items)} segments.")
            await self._emit_log(campaign, logs[-1])
            return BulkFixResponse(new_content=final_content, logs=logs, replacements=replacements_log)
        except Exception as e:
            logger.error(f"[PlagiarismSurgeon] AI Bulk Fix failed: {e}")
            return BulkFixResponse(new_content=cleaned_draft, logs=logs)
