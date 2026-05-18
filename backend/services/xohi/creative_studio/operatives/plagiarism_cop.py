import asyncio
import logging
import os
import re
import hashlib
import time
import gc
from datetime import datetime, timezone
from typing import List, Dict, Optional, Union, cast, Type
from difflib import SequenceMatcher
from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Agent
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, SearchKeyMixin
from backend.utils.http_client import get_http_client
from backend.services.xohi.creative_studio.models.schemas import (
    AgentResponse, AgentSignal, BulkFixRequest, BulkFixResponse,
    GoldMetadata, AnalysisMetrics, AnalysisCacheEntry,
    PlagiarismResult, CopyrightAnnotation
)
from backend.utils.noise_cleaner import noise_cleaner
from backend.utils.text import normalize_vn, extract_readable_text, is_json
from .plagiarism_refiner import PlagiarismRefiner
# [CNS V90.0] Shared Search Cache — tiết kiệm 50% Google quota với SEO
from .shared_search_cache import get_or_fetch as _cached_search
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.shields.service import shield_service

# ══════════════════════════════════════════════════════════════
# ELITE V2.2 CONSTANTS — Copyright Logic
# ══════════════════════════════════════════════════════════════
# Ngưỡng rủi ro: score < RISK_HIGH_THRESHOLD → HIGH risk; score < RISK_MEDIUM_THRESHOLD → MEDIUM risk
RISK_HIGH_THRESHOLD = 0.65
RISK_MEDIUM_THRESHOLD = 0.90
INTERNAL_DEDUP_PENALTY = 0.02
MAX_COMPETITOR_FETCH = 5
MAX_PARAGRAPHS_ANALYZE = 1000
DEFAULT_SIMILARITY_THRESHOLD = 0.75
RECON_TIMEOUT_SECONDS = 10.0
COMPETITOR_TIMEOUT_SECONDS = 5.0
MAX_SNIPPET_CHARS = 3000

class PlagiarismTaskRequest(BaseModel):
    campaign_id: str
    force: bool = False

logger = logging.getLogger("api-gateway")

class PlagiarismCop(BaseAgentOperative, SearchKeyMixin):
    """
    Step 5 (Auto) + On-Demand (Step 4): AI-powered Semantic Copyright Check.
    Elite V2.2: Context-Aware with Neural Prompt Orchestration (NPO).
    """
    agent_id_class = "plagiarism_cop"
    _plagiarism_semaphore = asyncio.Semaphore(4)

    def __init__(self, agent_id: str = "plagiarism_cop", threshold: float = DEFAULT_SIMILARITY_THRESHOLD, **kwargs: object):
        super().__init__(agent_id=agent_id)
        self.threshold = threshold
        self._agent = Agent(output_type=PlagiarismResult, retries=3)
        self._refiner = PlagiarismRefiner()

    async def chat(self, request: object, **kwargs: object) -> Union[PlagiarismResult, AgentResponse]:
        """Standardized Heritage Entry (V2.2). Maps to self.analyze."""
        if isinstance(request, ContentCampaign):
            return await self.analyze(request, force=bool(kwargs.get("force", False)))
        # Fallback for generic calls (duck typing)
        return await self.analyze(cast(ContentCampaign, request), **kwargs) # type: ignore

    def get_schema(self) -> Optional[Type[BaseModel]]:
        return PlagiarismTaskRequest

    async def process_brain_logic(self, request: PlagiarismTaskRequest, db: AsyncSession) -> PlagiarismResult:
        """
        Elite V2.2: Async Execution logic for arq Worker.
        Fetches campaign from DB and runs full analysis.
        """
        repo = ContentCampaignRepository(session=db)
        campaign = await repo.get(request.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {request.campaign_id} not found")
            
        # Run the heavy analysis
        result = await self.analyze(campaign, force=request.force)
        
        # Elite V2.2 Persistence: Strategy 6 - Persistent results in DB
        gold = dict(campaign.gold_metadata or {})
        cache = dict(gold.get("analysis_cache", {}))
        metrics = dict(gold.get("analysis_metrics", {}))

        content_hash = hashlib.sha256((campaign.draft_content or "").encode('utf-8')).hexdigest()
        cache["copyright"] = {"hash": content_hash, "data": result.model_dump(), "at": datetime.now(timezone.utc).isoformat()}
        metrics["unique_score"], metrics["copyright_risk"] = result.uniqueness_score, result.risk_level
        
        gold["analysis_cache"], gold["analysis_metrics"] = cache, metrics
        campaign.gold_metadata, campaign.unique_score = gold, result.uniqueness_score
        flag_modified(campaign, "gold_metadata")
        
        await repo.update(campaign)
        return result

    async def bulk_fix(self, campaign: ContentCampaign, req: BulkFixRequest) -> BulkFixResponse:
        return await self._refiner.bulk_fix(campaign, req)

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        campaign = await repo.get(campaign_id)
        if not campaign: return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")
        
        original_draft = campaign.draft_content or ""
        current_draft = extract_readable_text(original_draft)
        clean_draft = await noise_cleaner.clean(current_draft, mode="aggressive", strip_html=False)
        if clean_draft != current_draft and not is_json(original_draft):
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
        
        gc.collect()
        return AgentResponse(signal=AgentSignal.PROCEED_NEXT, message=f"✅ Hoàn tất — {result.verdict}", data={"score": result.uniqueness_score, "risk_level": result.risk_level, "annotations": [a.model_dump() for a in result.annotations], "verdict": result.verdict, "gold_metadata": gold})

    # Heritage Mixin handles _emit_progress

    async def analyze(self, campaign: ContentCampaign, force: bool = False) -> PlagiarismResult:
        logger.info(f"💓 [PlagiarismCop] Diving into copyright analysis for campaign {getattr(campaign, 'id', 'adhoc')}")
        async with self._plagiarism_semaphore:
            start_time = time.perf_counter()
            
            # CNS V90.5: Trình sát bắt đầu
            logger.warning(f"🕵️ [PlagiarismCop] Phân tích bắt đầu cho Campaign: {getattr(campaign, 'id', 'adhoc')}")
            
            now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
            # Đảm bảo logs luôn là list, tránh NoneType crash ở dòng 186
            logs: list[str] = [f"🚀 [{now_str}] Initializing Neural Copyright Engine (XoHi 2026)..."]
            await self._emit_progress(campaign, logs[-1])

            draft = extract_readable_text(campaign.draft_content or "")
            kw = campaign.get_gold_val("primary_keyword", "")
            logger.warning(f"📄 [PlagiarismCop] Input: Draft={len(draft)} chars, Keyword='{kw}'")
            
            if not kw and not draft:
                logger.warning("⚠️ [PlagiarismCop] Aborting: Missing draft and keyword.")
                return PlagiarismResult(uniqueness_score=1.0, risk_level="LOW", flagged_sentences=[], annotations=[], similar_sources=[], verdict="Thiếu dữ liệu (Chưa có Topic/Keyword).", logs=logs)

            word_count = len(draft.split())
            self.current_step = 0
            logs.append(f"🔍 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [NFC] Normalizing {word_count} words... cleaning noise & artifacts.")
            await self._emit_progress(campaign, logs[-1])
            
            logger.warning(f"🧹 [PlagiarismCop] Starting [NFC] Noise Cleaner (word_count={word_count})...")
            plain = await noise_cleaner.clean(draft, mode="aggressive", strip_html=False)
            logger.warning(f"✅ [PlagiarismCop] Noise Cleaner complete. Plain text: {len(plain)} chars.")

            logs.append(f"📡 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [DEDUP] Internal Cross-Paragraph Synthesis... scanning for internal redundancy.")
            await self._emit_progress(campaign, logs[-1])
            
            logger.warning("📡 [PlagiarismCop] Starting Internal Deduplication...")
            seen, deduped, i_annots = set(), [], []
            for para in self._refiner._split_into_paragraphs(plain)[:MAX_PARAGRAPHS_ANALYZE]:
                norm = normalize_vn(para)
                if len(norm) < 10: deduped.append(para); continue
                if norm not in seen: seen.add(norm); deduped.append(para)
                else: i_annots.append(CopyrightAnnotation(text=para, reason="Đoạn lặp lại trong bài", source_url="internal", severity="high", type="internal-dedup"))

            logger.warning(f"📊 [PlagiarismCop] Deduplication complete: {len(deduped)} unique paragraphs, {len(i_annots)} internal duplicates.")

            if not kw:
                logger.warning("📡 [PlagiarismCop] No keyword. Skipping Google RECON.")
                logs.append("[RECON] No topic/keyword found. Skipping Google Recon, proceeding with internal scan.")
                await self._emit_progress(campaign, logs[-1])
                comps = []
            else:
                self.current_step = 1
                logger.warning(f"📡 [PlagiarismCop] Initiating Google RECON for: '{kw}'")
                logs.append(f"[RECON] Initiating Google Search Recon for: '{kw}'")
                await self._emit_progress(campaign, logs[-1])
                comps = await self._fetch_competitor_snippets(campaign, kw, logs=logs)
                logger.warning(f"✅ [PlagiarismCop] Google RECON fetched {len(comps)} competitor snippets.")

            logs.append(f"🧠 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [BRAIN] Loading competitive landscape into Neural Core...")
            await self._emit_progress(campaign, logs[-1])
            try:
                self.current_step = 2
                logs.append("[SEMANTIC] Analyzing Information Gain & Structural Risks with Gemini AI...")
                await self._emit_progress(campaign, logs[-1])
                
                # [CNS-V89] Resolve Context via Centralized Intelligence
                context = await self._resolve_xohi_context(campaign, draft, "copyright")
                if context.get("log_msg"):
                    await self._emit_progress(campaign, context["log_msg"])
                
                # CNS V90.5: Breadcrumbs cho Sếp check terminal
                logger.warning(f"🛡️ [PlagiarismCop] Context resolved: {context.get('role_assignment')}")
                
                logs.append(f"🛡️ [ROLE] Đã xác nhận phân vai tác chiến: {context['role_assignment']}")
                await self._emit_progress(campaign, logs[-1])
                
                logs.append(f"🛡️ [SHIELD] Đã kích hoạt SGE Shield V2.1 (Anti-AI Footprint)")
                await self._emit_progress(campaign, logs[-1])
                
                is_adhoc = str(getattr(campaign, "id", "adhoc")) == "adhoc"
                logs.append(f"🛡️ [SAFETY] Chế độ Ad-hoc Safety: {'ACTIVE' if is_adhoc else 'CAMPAIGN_MODE'}")
                await self._emit_progress(campaign, logs[-1])
                
                logger.warning("🧠 [PlagiarismCop] Initiating Neural Synthesis (Gemini)...")
                
                shield = shield_service.get_shield_component(seed=str(getattr(campaign, "id", "adhoc")))
                composer.register_component(shield)
                
                logger.warning("🎨 [PlagiarismCop] Building Prompt Package...")
                
                # ELITE V2.2: Use extra_components to maintain thread-safety
                system_prompt = composer.compose("copyright_analysis", context=context, extra_components=[shield.id])
                
                logger.warning("📡 [PlagiarismCop] Sending to Neural Core (Brain)...")
                # CNS V91.2: Reduce input pressure — 50k→25k chars to free output token budget
                # Gemini context window is shared between input+output. Large input = compressed output = truncated verdict
                content_input = ('\n'.join(deduped))[:25000]
                # Cap competitor snippets: each MAX_SNIPPET_CHARS=3000, max 5 comps = 15000 chars max
                comps_input = '\n'.join(c[:MAX_SNIPPET_CHARS] for c in comps[:MAX_COMPETITOR_FETCH])
                prompt = f"""[BÀI VIẾT CỦA BẠN]:\n{content_input}\n\n[ĐỐI THỦ CẠNH TRANH]:\n{comps_input}"""
                logger.warning(f"📡 [PlagiarismCop] Prompt size: {len(prompt)} chars. Awaiting Brain Response...")
                res = await self.bridge.run(
                    self._agent, prompt,
                    system_prompt=system_prompt,
                    force=force,
                    role="brain",
                    timeout=180.0,
                    safety_none=True,
                    # CNS V91.2: CRITICAL FIX — key was 'max_output_tokens' (WRONG/ignored), must be 'max_tokens'
                    # PydanticAI ModelSettings TypedDict only has 'max_tokens' field, others are silently ignored
                    model_settings={"max_tokens": 8192}
                )
                raw = res
                logger.warning(f"✅ [PlagiarismCop] Brain returned. Type: {type(raw).__name__}")

                if hasattr(raw, 'data') and not hasattr(raw, 'uniqueness_score'):
                    raw = raw.data
                    logger.warning("📦 [PlagiarismCop] Unpacked raw.data")

                if hasattr(raw, 'uniqueness_score'):
                    if raw.uniqueness_score > 1.0:
                        raw.uniqueness_score = raw.uniqueness_score / 100.0
                    logger.warning(f"📊 [PlagiarismCop] Final Uniqueness Score: {raw.uniqueness_score}")

                if hasattr(raw, 'annotations'):
                    annots = list(raw.annotations or [])
                    for ian in i_annots:
                        raw.uniqueness_score = max(0.0, raw.uniqueness_score - INTERNAL_DEDUP_PENALTY)
                        annots.append(ian)
                    raw.annotations = annots
                    raw.risk_level = "HIGH" if raw.uniqueness_score < RISK_HIGH_THRESHOLD else ("MEDIUM" if raw.uniqueness_score < RISK_MEDIUM_THRESHOLD else "LOW")
                
                duration = time.perf_counter() - start_time
                self.current_step = 3
                msg = f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [QUANTUM] Kiểm tra tác quyền hoàn tất! ({duration:.1f}s) ĐÃ XỬ LÝ XONG"
                logs.append(msg)
                await self._emit_progress(campaign, msg)
                
                # Elite V2.2: Discreet timestamp integration
                report_time = datetime.now(timezone.utc).strftime('%H:%M:%S %d/%m/%Y')
                time_badge = f"> ⏱️ **Báo cáo lập lúc:** `{report_time}`\n\n"
                
                # CNS V92.1: Reset verdict field TRƯỚC — chặn AI leak "---"/whitespace vào fallback
                raw.verdict = ""

                if hasattr(raw, 'verdict_gap') or hasattr(raw, 'verdict_evidence') or hasattr(raw, 'verdict_strategy'):
                    # .strip() bắt buộc: loại whitespace-only strings (truthy nhưng render rỗng)
                    gap      = (getattr(raw, 'verdict_gap', '')      or '').strip()
                    evidence = (getattr(raw, 'verdict_evidence', '') or '').strip()
                    strategy = (getattr(raw, 'verdict_strategy', '') or '').strip()

                    # CNS V92.3 DEBUG — dump để xác nhận AI có trả dữ liệu không
                    logger.warning(f"🔬 [PlagiarismCop] gap={len(gap)}c | ev={len(evidence)}c | strat={len(strategy)}c")
                    logger.warning(f"🔬 [PlagiarismCop] gap_preview={repr(gap[:120])}")

                    combined = ""
                    if gap or evidence or strategy:
                        # CNS V92.3: Bỏ \n---\n\n khỏi header — đây là nguồn gốc dấu '---' trơ khi section rỗng
                        combined += f"### 🛡️ ⚔️ BẢN TRÌNH BÁO CHIẾN LƯỢC BẢN QUYỀN | {context.get('role_assignment', 'Chuyên gia')}\n\n"
                        if gap:      combined += f"#### 🔍 [1. LUẬN ĐIỂM PHẢN BIỆN — CRITICAL GAP]\n\n{gap}\n\n"
                        if evidence: combined += f"#### 🔗 [2. HỒ SƠ CHỨNG CỨ VÀ NGHIÊN CỨU — EVIDENCE & RESEARCH FILE]\n\n{evidence}\n\n"
                        if strategy: combined += f"#### 💎 [3. CHIẾN LƯỢC TÁI CẤU TRÚC — RESTRUCTURING STRATEGY]\n\n{strategy}\n\n"
                    
                    if combined:
                        raw.verdict = time_badge + combined
                    else:
                        raw.verdict = time_badge + "⚠️ [BRAIN] AI không trả về nội dung phân tích — thử lại hoặc kiểm tra model."
                else:
                    raw.verdict = time_badge + (getattr(raw, 'verdict', '') or "⚠️ [BRAIN] Không có phản hồi nội dung phân tích.")
                
                if hasattr(raw, 'logs'): raw.logs = logs
                return raw
            except Exception as e:
                logger.warning(f"❌ [PlagiarismCop] Neural Engine Error: {str(e)}")
                
                # CNS V90.5: Emit feedback even in failure to avoid UI hang
                err_msg = "⚠️ [BRAIN] Neural Engine bận. Chuyển sang chế độ trinh sát cục bộ (Heuristic)..."
                logs.append(err_msg)
                await self._emit_progress(campaign, err_msg)
                
                h_res = await asyncio.to_thread(self._heuristic_analyze, deduped, comps, i_annots)
                msg = "✅ [NEURAL XOHI] Trinh sát hoàn tất! ĐÃ XỬ LÝ XONG"
                h_res.logs = logs + [msg]
                await self._emit_progress(campaign, msg)
                h_res.verdict = f"Hệ thống bận ({str(e)[:40]}). Đã kích hoạt Heuristic Mode của Neural XoHi để đảm bảo tiến độ."
                return h_res

    def _heuristic_analyze(self, deduped: list[str], comps: list[str], i_annots: list[CopyrightAnnotation]) -> PlagiarismResult:
        """R102: Heuristic Fallback — Phân tích cục bộ không dùng AI."""
        h_annots = list(i_annots)
        total_chars, matched_chars = sum(len(p) for p in deduped), 0
        comp_pool = normalize_vn("\n".join(comps))
        
        for p in deduped:
            if len(p) < 40: continue
            p_norm = normalize_vn(p)
            p_matched = False
            
            if p_norm in comp_pool:
                p_matched = True
            else:
                p_words = set(p_norm.split())
                if len(p_words) > 10:
                    pool_words = set(comp_pool[:10000].split())
                    intersect = p_words.intersection(pool_words)
                    if len(intersect) / len(p_words) > 0.85:
                        p_matched = True
            
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
            risk_level="HIGH" if score < RISK_HIGH_THRESHOLD else ("MEDIUM" if score < RISK_MEDIUM_THRESHOLD else "LOW"),
            flagged_sentences=[],
            annotations=h_annots,
            similar_sources=[],
            verdict=(
                f"### 🛡️ ⚔️ BẢN TRÌNH BÁO CHIẾN LƯỢC BẢN QUYỀN (HEURISTIC MODE)\n\n"
                f"#### 🔍 [1. LUẬN ĐIỂM PHẢN BIỆN — CRITICAL GAP]\n\n"
                f"- Hệ thống AI Neural đang tạm thời bận — đã kích hoạt chế độ trinh sát cục bộ (Local Heuristic) để đảm bảo tiến độ không gián đoạn.\n"
                f"- Kết quả sơ bộ dựa trên so sánh từ vựng (Jaccard + Token Overlap) với nội dung đối thủ đã thu thập.\n"
                f"- Phát hiện {len(h_annots)} đoạn có mức độ trùng lặp cao (>85% token overlap). Cần xem xét lại cấu trúc và ngôn ngữ.\n\n"
                f"#### 🔗 [2. HỒ SƠ CHỨNG CỨ — EVIDENCE FILE]\n\n"
                f"- Tổng số đoạn phân tích: {len(deduped)} đoạn độc lập.\n"
                f"- Đoạn trùng lặp nội bộ: {len(i_annots)} đoạn (penalized -0.02/đoạn).\n"
                f"- Đoạn trùng lặp với đối thủ: {len(h_annots) - len(i_annots)} đoạn (Heuristic detection).\n\n"
                f"#### 💎 [3. CHIẾN LƯỢC TÁI CẤU TRÚC — RESTRUCTURING STRATEGY]\n\n"
                f"- **Bước 1 — ĐỊNH VỊ CỐT LÕI**: Xem xét lại góc tiếp cận tổng thể. Tránh dùng cấu trúc mô tả tuyến tính (công dụng → thành phần → hướng dẫn) — đây là cấu trúc phổ biến nhất của đối thủ. Thay vào đó, hãy mở đầu bằng vấn đề thực tế của người dùng (Pain Point) rồi mới giới thiệu giải pháp.\n"
                f"- **Bước 2 — PHÂN BỔ 4 KHỐI (HOẶC BỘ KHUNG)**: Phân bổ lại nội dung theo 4 trụ cột (đối với bài viết) hoặc theo bộ khung chuẩn (Giới thiệu / Công dụng / Đối tượng / Cách sử dụng / Lưu ý / Bảo quản / Cam kết đối với sản phẩm). Đảm bảo thông tin truyền tải rõ ràng, đúng trọng tâm, ngắn gọn và không màu mè hoa lá hẹ.\n"
                f"- **Bước 3 — KẾ HOẠCH REWRITE**: (1) Thay thế toàn bộ các đoạn bị đánh dấu bằng ngôn ngữ gốc từ trải nghiệm thực tế. (2) Bổ sung dẫn chứng khoa học hoặc số liệu cụ thể. (3) Sử dụng giọng văn thương hiệu nhất quán thay vì ngôn ngữ generic. (4) Kiểm tra lại sau khi sửa bằng công cụ Neural Copyright để xác nhận điểm Uniqueness đạt >0.85."
            )
        )

    async def _fetch_competitor_snippets(self, campaign: ContentCampaign, keyword: str, logs: Optional[list[str]] = None) -> list[str]:
        """
        [CNS V90.0] Fetch competitor content with retry loop + shared cache.
        """
        self._ensure_search_keys()
        if not self.search_keys:
            if logs is not None: logs.append("❌ Thiếu API Key Search.")
            return ["(No API key)"]

        async def _do_fetch() -> list[str]:
            client = await get_http_client()
            for attempt in range(len(self.search_keys)):
                p = await self._get_search_pair()
                try:
                    logger.warning(f"🔍 [PlagiarismCop] Search Attempt {attempt + 1}/{len(self.search_keys)} using CX: {p['cx'][:8]}...")
                    resp = await client.get(
                        "https://www.googleapis.com/customsearch/v1",
                        params={"key": p["key"], "cx": p["cx"], "q": keyword, "num": MAX_COMPETITOR_FETCH},
                        timeout=RECON_TIMEOUT_SECONDS
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("items", [])
                        logger.warning(f"✅ [PlagiarismCop] Google Search Success. Found {len(items)} items.")
                        if not items:
                            if logs is not None: logs.append("❓ Không tìm thấy kết quả nào trên Google.")
                            return ["(No results)"]

                        await self._emit_progress(campaign, f"[RECON] Discovered {len(items)} competitor sites. Starting deep inspection...")
                        async def _c(it: dict, idx: int):
                            url = it.get("link", "")
                            if not url.startswith("http"): return it.get("snippet", "")
                            try:
                                logger.warning(f"📡 [PlagiarismCop] Scrape Start [{idx+1}/5]: {url[:50]}...")
                                r = await client.get(url, timeout=COMPETITOR_TIMEOUT_SECONDS, follow_redirects=True)
                                if r.status_code == 200:
                                    logger.warning(f"✅ [PlagiarismCop] Scrape Success: {url[:50]}")
                                    b = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', r.text, flags=re.IGNORECASE|re.DOTALL)
                                    b = re.sub(r'<[^>]+>', ' ', b)
                                    return f"URL: {url}\nContent: {re.sub(r'\\s+', ' ', b).strip()[:MAX_SNIPPET_CHARS]}"
                                else:
                                    logger.warning(f"⚠️ [PlagiarismCop] Scrape Failed (Status {r.status_code}): {url[:50]}")
                            except Exception as e:
                                logger.warning(f"❌ [PlagiarismCop] Scrape Error: {str(e)[:50]}")
                                pass
                            return f"URL: {url}\nSnippet: {it.get('snippet', '')}"


                        rs = await asyncio.gather(*[_c(it, i) for i, it in enumerate(items[:5])], return_exceptions=True)
                        valid_rs = [r if isinstance(r, str) else "(Snippet only)" for r in rs]
                        msg = f"[RECON] Competitor content ingestion complete ({len(valid_rs)} sources)."
                        await self._emit_progress(campaign, msg)
                        if logs is not None: logs.append(msg)
                        return valid_rs

                    elif resp.status_code in [429, 403]:
                        self.logger.warning(f"[PlagiarismCop] Search Key Outage ({resp.status_code}), rotating...")
                        continue  # Try next key
                    else:
                        err_hint = f"Google Error {resp.status_code}"
                        if logs is not None: logs.append(f"❌ {err_hint}")
                        return [f"({err_hint})"]

                except Exception as e:
                    self.logger.error(f"[PlagiarismCop] Search connection error: {e}")
                    continue  # Try next key

            if logs is not None: logs.append("❌ Cạn kiệt API Key Search (Tất cả đều lỗi/hết hạn).")
            return ["(All search keys failed)"]

        results = await _cached_search(query=keyword, fetch_fn=_do_fetch, num=MAX_COMPETITOR_FETCH)
        if not results:
            if logs is not None: logs.append("❌ Không lấy được kết quả từ Google.")
        return results if results else ["(No results)"]

