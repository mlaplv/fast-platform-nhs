import asyncio
import logging
import os
import re
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, cast
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent
from sqlalchemy.orm.attributes import flag_modified
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import (
    AgentResponse, AgentSignal, BulkFixRequest, BulkFixResponse,
    GoldMetadata, AnalysisMetrics, AnalysisCacheEntry,
    PlagiarismResult, CopyrightAnnotation
)
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.http_client import get_http_client
from backend.utils.noise_cleaner import noise_cleaner
from backend.utils.text import normalize_vn
from .plagiarism_prompts import PLAGIARISM_PROMPT
from .plagiarism_surgeon import PlagiarismSurgeon

logger = logging.getLogger("api-gateway")

class PlagiarismCop:
    """
    Step 5 (Auto) + On-Demand (Step 4): AI-powered Semantic Copyright Check.
    Complying with Martial Law (<300 lines) by delegating to specialized surgeon.
    """
    _plagiarism_semaphore = asyncio.Semaphore(1)
    _key_lock = asyncio.Lock()
    _key_idx = 0

    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.search_keys = []
        for i in ["", "_1", "_2"]:
            k, cx = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}"), os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
            if k and cx: self.search_keys.append({"key": k, "cx": cx})
        
        self._agent = Agent(output_type=PlagiarismResult, system_prompt=PLAGIARISM_PROMPT, retries=3)
        self._surgeon = PlagiarismSurgeon()

    async def bulk_fix(self, campaign: ContentCampaign, req: BulkFixRequest) -> BulkFixResponse:
        return await self._surgeon.bulk_fix(campaign, req)

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        campaign = await repo.get(campaign_id)
        if not campaign: return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")
        
        current_draft = campaign.draft_content or ""
        clean_draft = await noise_cleaner.clean(current_draft, mode="aggressive", strip_html=False)
        if clean_draft != current_draft:
            campaign.draft_content = clean_draft
            await repo.update(campaign)

        result = await self.analyze(campaign)
        gold = cast(GoldMetadata, dict(campaign.gold_metadata or {}))
        cache = dict(gold.get("analysis_cache", {}))
        metrics = dict(gold.get("analysis_metrics", {}))

        content_hash = hashlib.sha256(clean_draft.encode('utf-8')).hexdigest()
        cache["copyright"] = {"hash": content_hash, "data": result.model_dump(), "at": datetime.now(timezone.utc).isoformat()}
        metrics["unique_score"], metrics["copyright_risk"] = result.uniqueness_score, result.risk_level
        gold["analysis_cache"], gold["analysis_metrics"] = cache, metrics
        campaign.gold_metadata, campaign.unique_score = gold, result.uniqueness_score
        flag_modified(campaign, "gold_metadata")
        await repo.update(campaign)

        if result.risk_level == "HIGH":
            return AgentResponse(signal=AgentSignal.REDO_PREVIOUS, message="🚨 Nguy cơ đạo văn cao.", data={"score": result.uniqueness_score, "risk_level": result.risk_level, "gold_metadata": gold})
        return AgentResponse(signal=AgentSignal.PROCEED_NEXT, message=f"✅ Hoàn tất — {result.verdict}", data={"score": result.uniqueness_score, "risk_level": result.risk_level, "annotations": [a.model_dump() for a in result.annotations], "verdict": result.verdict, "gold_metadata": gold})

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

    async def analyze(self, campaign: "ContentCampaign", force: bool = False) -> PlagiarismResult:
        logger.info(f"💓 [PlagiarismCop] Diving into copyright analysis for campaign {campaign.id}")
        """
        Phase 1: Search (Google Custom Search with Key Rotation)
        Phase 2: Scrape (Fetch top 3 competitor contents)
        Phase 3: AI Analysis (Plagiarism Annotations & Uniqueness Score)
        Phase 4: Heuristic Fallback (If AI fails)
        """
        logs = ["🔍 Khởi động hệ thống rà soát bản quyền (Neural V82.8)..."]
        await self._emit_log(campaign, logs[-1])
        
        # If force is true, we should tell the bridge to try even if some keys are flagged
        # But for now, we just pass it down.
        
        async with self._plagiarism_semaphore: draft = campaign.draft_content or ""
        kw = campaign.get_gold_val("primary_keyword", "")
        if not kw and not draft:
            return PlagiarismResult(uniqueness_score=1.0, risk_level="LOW", flagged_sentences=[], annotations=[], similar_sources=[], verdict="Thiếu dữ liệu (Chưa có Topic/Keyword).", logs=logs)

        logs.append("🧹 Đang tiền xử lý...")
        await self._emit_log(campaign, logs[-1])
        plain = await noise_cleaner.clean(draft, mode="aggressive", strip_html=False)
        
        logs.append("🧠 Đang rà soát trùng lặp nội bộ...")
        await self._emit_log(campaign, logs[-1])
        seen, deduped, i_annots = set(), [], []
        for para in self._surgeon._split_into_paragraphs(plain)[:200]:
            norm = normalize_vn(para)
            if len(norm) < 10: deduped.append(para); continue
            if norm not in seen: seen.add(norm); deduped.append(para)
            else: i_annots.append(CopyrightAnnotation(text=para[:200], reason="Đoạn lặp lại trong bài", source_url="internal", severity="high", type="internal-dedup"))

        logs.append(f"📡 Đang trinh sát nguồn đối thủ cho: '{kw}'...")
        await self._emit_log(campaign, logs[-1])
        comps = await self._fetch_competitor_snippets(campaign, kw, logs=logs)
        
        logs.append("🧠 Đang nạp dữ liệu vào Neural Engine...")
        await self._emit_log(campaign, logs[-1])
        try:
            prompt = f"[BÀI VIẾT]\n{('\n'.join(deduped))[:12000]}\n\n[ĐỐI THỦ]\n{'\n'.join(comps)}"
            res = await trinity_bridge.run(self._agent, prompt, force=force)
            
            # Phase 3.1: Strict Typing & Result Extraction (V89.1 Fix: Use .data or .output)
            raw = res.data if hasattr(res, "data") else (res.output if hasattr(res, "output") else res)
            
            # Final Safety: If for some Reason trinity_bridge returned the raw AgentRunResult
            # outside the casted object, we MUST extract its data to avoid 'model_dump' errors.
            if hasattr(raw, 'data') and not hasattr(raw, 'uniqueness_score'):
                raw = raw.data

            if hasattr(raw, 'annotations'):
                annots = list(raw.annotations or [])
                for ian in i_annots:
                    # Deeply link internal dedup annotations
                    raw.uniqueness_score = max(0.0, raw.uniqueness_score - 0.02)
                    annots.append(ian)
                raw.annotations = annots
                raw.risk_level = "HIGH" if raw.uniqueness_score < 0.65 else ("MEDIUM" if raw.uniqueness_score < 0.9 else "LOW")
            
            if hasattr(raw, 'logs'): raw.logs = logs
            return raw
        except Exception as e:
            logger.error(f"[PlagiarismCop] Neural Engine Error: {str(e)}", exc_info=True)
            if logs is not None: logs.append(f"📡 AI đang bận, kích hoạt Heuristic Mode (Dò tìm cục bộ)...")
            h_res = self._heuristic_analyze(deduped, comps, i_annots)
            h_res.logs = logs
            h_res.verdict = f"Hệ thống bận ({str(e)[:40]}). Kết quả dựa trên đối soát cục bộ."
            return h_res

    def _heuristic_analyze(self, deduped: List[str], comps: List[str], i_annots: List[CopyrightAnnotation]) -> PlagiarismResult:
        """R102: Heuristic Fallback — Phân tích cục bộ không dùng AI."""
        from difflib import SequenceMatcher
        h_annots = list(i_annots)
        total_chars, matched_chars = sum(len(p) for p in deduped), 0
        
        # Flatten competitor content for searching
        comp_pool = "\n".join(comps)
        
        for p in deduped:
            if len(p) < 40: continue
            # Split into chunks of 100 chars for searching if the paragraph is long
            chunks = [p[i:i+100] for i in range(0, len(p), 100)]
            p_matched = False
            for chunk in chunks:
                if len(chunk) < 20: continue
                # Look for exact match first
                if chunk in comp_pool:
                    p_matched = True; break
                # Then fuzzy (expensive, so only if short paragraph)
                if len(p) < 300:
                    s = SequenceMatcher(None, p, comp_pool[:5000]) # Sample pool to stay fast
                    if s.quick_ratio() > 0.7 and s.ratio() > 0.8:
                        p_matched = True; break
            
            if p_matched:
                matched_chars += len(p)
                h_annots.append(CopyrightAnnotation(
                    text=p[:200], 
                    reason="Trùng khớp với nội dung trên Google (Heuristic)", 
                    source_url="external", 
                    severity="high", 
                    type="plagiarism"
                ))

        score = max(0.0, 1.0 - (matched_chars / (total_chars or 1)))
        return PlagiarismResult(
            uniqueness_score=score,
            risk_level="HIGH" if score < 0.7 else ("MEDIUM" if score < 0.9 else "LOW"),
            flagged_sentences=[],
            annotations=h_annots,
            similar_sources=[],
            verdict="Kết quả sơ bộ (Local Heuristic)."
        )

    async def _fetch_competitor_snippets(self, campaign: ContentCampaign, keyword: str, logs: Optional[List[str]] = None) -> List[str]:
        if not self.search_keys:
            if logs is not None: logs.append("❌ Thiếu API Key Search.")
            return ["(No API key)"]

        client = await get_http_client()
        # R105: Automated Key Rotation with Retry Loop
        for attempt in range(len(self.search_keys)):
            p = await self._get_search_pair()
            try:
                resp = await client.get("https://www.googleapis.com/customsearch/v1", params={"key": p["key"], "cx": p["cx"], "q": keyword, "num": 5}, timeout=10.0)
                
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("items", [])
                    if not items:
                        if logs is not None: logs.append("❓ Không tìm thấy kết quả nào trên Google.")
                        return ["(No results)"]
                    
                    # Success: start content fetching
                    await self._emit_log(campaign, f"🕵️ Phát hiện {len(items)} nguồn dữ liệu khả nghi. Đang thẩm định...")
                    async def _c(it: dict, idx: int):
                        url = it.get("link", "")
                        if not url.startswith("http"): return it.get("snippet","")
                        try:
                            await self._emit_log(campaign, f"🌐 Trinh sát [{idx+1}/5]: {url[:45]}...")
                            # Use shorter timeout for competitor sites
                            r = await client.get(url, timeout=5.0)
                            if r.status_code == 200:
                                b = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', r.text, flags=re.IGNORECASE|re.DOTALL)
                                b = re.sub(r'<[^>]+>', ' ', b)
                                return f"URL: {url}\nContent: {re.sub(r'\s+', ' ', b).strip()[:3000]}"
                        except Exception as e:
                            logger.debug(f"[PlagiarismCop] Failed to fetch {url}: {e}")
                        return f"URL: {url}\nSnippet: {it.get('snippet','')}"

                    rs = await asyncio.gather(*[_c(it, i) for i, it in enumerate(items[:5])], return_exceptions=True)
                    valid_rs = [r if isinstance(r, str) else "(Snippet only)" for r in rs]
                    msg = f"📡 Đã tải xong nội dung từ {len(valid_rs)} website đối thủ."
                    await self._emit_log(campaign, msg)
                    if logs is not None: logs.append(msg)
                    return valid_rs

                elif resp.status_code in [429, 403]:
                    logger.warning(f"[PlagiarismCop] Search Key Outage ({resp.status_code}), rotating...")
                    continue # Try next key
                else:
                    err_hint = f"Google Error {resp.status_code}"
                    if logs is not None: logs.append(f"❌ {err_hint}")
                    return [f"({err_hint})"]

            except Exception as e:
                logger.error(f"[PlagiarismCop] Search connection error: {e}")
                continue # Try next key

        if logs is not None: logs.append("❌ Cạn kiệt API Key Search (Tất cả đều lỗi/hết hạn).")
        return ["(All search keys failed)"]

    async def _get_search_pair(self):
        if not self.search_keys: return None
        async with self._key_lock:
            pair = self.search_keys[self.__class__._key_idx % len(self.search_keys)]
            self.__class__._key_idx += 1
        return pair
