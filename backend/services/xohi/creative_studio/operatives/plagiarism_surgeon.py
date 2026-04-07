import re
import asyncio
import logging
from typing import List, Dict, Optional, Tuple, cast, Set
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.xohi.creative_studio.models.schemas import (
    BulkFixRequest, BulkFixResponse, AtomicFixResponse, SurgicalSnippetFix
)
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner
from backend.utils.text import normalize_vn
from backend.services.xohi.creative_studio.utils.stitcher import surgical_stitch
from .plagiarism_prompts import PLAGIARISM_SURGEON_PROMPT

logger = logging.getLogger("api-gateway")

RE_DIGIT = re.compile(r'\d+')

class PlagiarismSurgeon:
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
        logs = ["🔍 Khởi động hệ thống phẫu thuật nội dung..."]
        draft = await noise_cleaner.clean(campaign.draft_content or "", mode="light", strip_html=False)
        raw_paragraphs = self._split_into_paragraphs(draft)
        paragraphs = raw_paragraphs[:500]

        THRESHOLD = 0.82
        kept: List[Tuple[str, set[str]]] = []
        for para in paragraphs:
            if len(para) < 15:
                kept.append((para, set()))
                continue
            tokens = self._tokenize(para)
            if not any(self._jaccard(tokens, k_tok) >= THRESHOLD for _, k_tok in kept if k_tok):
                kept.append((para, tokens))
            else:
                logs.append(f"✂️ Đã cắt bỏ đoạn văn trùng lặp nội bộ: \"{para[:40]}...\"")

        # Deterministic Sentence-Level Dedup
        seen_norms: set[str] = set()
        dedup_count = 0
        final_paragraphs = []
        for para, _ in kept:
            para_sentences = [s.strip() for s in re.split(r'(?<=[.!?。])[\s\n]+', para) if s.strip()]
            para_kept = []
            for s in para_sentences:
                norm = normalize_vn(s)
                if len(norm) < 40: para_kept.append(s); continue
                if norm not in seen_norms:
                    seen_norms.add(norm)
                    para_kept.append(s)
                else:
                    dedup_count += 1
                    logs.append(f"✂️ Đã loại bỏ câu lặp nội bộ: \"{s[:40]}...\"")
            if para_kept: final_paragraphs.append(" ".join(para_kept))

        cleaned_draft = "\n\n".join(final_paragraphs)
        
        # AI Surgeon for external plagiarism
        annots = req.annotations if isinstance(req.annotations, list) else []
        all_annots = [a for a in annots if (a.get("text") or a.get("reason")) and len(str(a.get("text",""))) > 5]
        
        if not all_annots:
            return BulkFixResponse(new_content=cleaned_draft, logs=logs)

        snippet_list = ""
        valid_items = []
        for i, a in enumerate(all_annots[:40]):
            txt = await noise_cleaner.clean(str(a.get('text', '')), mode="light", strip_html=False)
            snippet_list += f"\n[ID {i+1}]:\n- Cần sửa: \"{txt}\"\n- Lỗi: {a.get('reason','')}\n"
            valid_items.append({"id": i+1, "old_text": txt})

        logs.append(f"🧠 Đang xử lý {len(valid_items)} đoạn vi phạm qua AI...")
        bulk_prompt = f"{PLAGIARISM_SURGEON_PROMPT}\n\n[DANH SÁCH CẦN SỬA]\n{snippet_list}"
        
        try:
            res = await trinity_bridge.run(self._atomic_surgeon_agent, bulk_prompt, role="fast", timeout=120.0)
            raw_data = res
            final_content = cleaned_draft
            replacements_made = 0
            replacements_log = []
            if hasattr(raw_data, "replacements"):
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
                            logs.append(f"✅ Đã phẫu thuật xong: \"{old_txt[:30]}...\"")
            
            logs.append(f"🏅 Hoàn tất! Đã xử lý {replacements_made + dedup_count} điểm yếu.")
            return BulkFixResponse(new_content=final_content, logs=logs, replacements=replacements_log)
        except Exception as e:
            logger.error(f"[PlagiarismSurgeon] AI Bulk Fix failed: {e}")
            return BulkFixResponse(new_content=cleaned_draft, logs=logs)
