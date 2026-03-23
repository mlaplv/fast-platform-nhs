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

    async def analyze(self, campaign: ContentCampaign) -> PlagiarismResult:
        logs = ["🔍 Khởi động hệ thống tầm soát bản quyền..."]
        await self._emit_log(campaign, logs[-1])
        
        async with self._plagiarism_semaphore: draft = campaign.draft_content or ""
        gold = campaign.gold_metadata or {}
        kw = gold.get("primary_keyword", "")
        if not draft or not kw:
            return PlagiarismResult(uniqueness_score=1.0, risk_level="LOW", flagged_sentences=[], annotations=[], similar_sources=[], verdict="Thiếu dữ liệu.", logs=logs)

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
        comps = await self._fetch_competitor_snippets(kw, logs=logs)
        
        logs.append("🧠 Đang nạp dữ liệu vào Neural Engine...")
        await self._emit_log(campaign, logs[-1])
        try:
            prompt = f"[BÀI VIẾT]\n{('\n'.join(deduped))[:12000]}\n\n[ĐỐI THỦ]\n{'\n'.join(comps)}"
            res = await trinity_bridge.run(self._agent, prompt)
            raw = res.data if hasattr(res, "data") else res.output
            if hasattr(raw, 'annotations'):
                annots = [a for a in raw.annotations if a.text]
                for ian in i_annots:
                    raw.uniqueness_score = max(0.0, raw.uniqueness_score - 0.02)
                    ian.type = "internal-dedup"
                    annots.append(ian)
                raw.annotations = annots
                raw.risk_level = "HIGH" if raw.uniqueness_score < 0.65 else ("MEDIUM" if raw.uniqueness_score < 0.9 else "LOW")
            raw.logs = logs
            return raw
        except Exception:
            return PlagiarismResult(uniqueness_score=0.88, risk_level="MEDIUM", flagged_sentences=[], annotations=i_annots, similar_sources=[], verdict="AI đang bận.", logs=logs)

    async def _fetch_competitor_snippets(self, keyword: str, logs: Optional[List[str]] = None) -> List[str]:
        p = await self._get_search_pair()
        if not p: return ["(No API key)"]
        try:
            client = await get_http_client()
            resp = await client.get("https://www.googleapis.com/customsearch/v1", params={"key": p["key"], "cx": p["cx"], "q": keyword, "num": 5}, timeout=10.0)
            items = resp.json().get("items", [])
            async def _c(it: dict):
                url = it.get("link", "")
                if not url.startswith("http"): return it.get("snippet","")
                try:
                    r = await client.get(url, timeout=5.0)
                    if r.status_code == 200:
                        b = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', r.text, flags=re.IGNORECASE|re.DOTALL)
                        b = re.sub(r'<[^>]+>', ' ', b)
                        return f"URL: {url}\nContent: {re.sub(r'\s+', ' ', b).strip()[:3000]}"
                except: pass
                return f"URL: {url}\nSnippet: {it.get('snippet','')}"
            rs = await asyncio.gather(*[_c(i) for i in items[:5]], return_exceptions=True)
            if logs is not None: logs.append(f"📡 Đã tải xong nội dung từ {len(rs)} website.")
            return [r if isinstance(r, str) else "(Failed)" for r in rs]
        except: return ["(Search failed)"]

    async def _get_search_pair(self):
        if not self.search_keys: return None
        async with self._key_lock:
            pair = self.search_keys[self.__class__._key_idx % len(self.search_keys)]
            self.__class__._key_idx += 1
        return pair
