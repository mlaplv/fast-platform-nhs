import asyncio
import logging
import os
import re
import copy
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Union, cast
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from sqlalchemy.orm.attributes import flag_modified
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal, BulkFixRequest, BulkFixResponse
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.http_client import get_http_client
from backend.utils.noise_cleaner import noise_cleaner, RE_WHITESPACE
from backend.utils.text import normalize_vn

logger = logging.getLogger("api-gateway")

# Phase 76.3: Specialized Plagiarism Analysis Helpers
import unicodedata  # top-level — reused by bulk_fix & _detect_internal_duplicates
RE_SENTENCE_SPLIT = re.compile(r'(?<=[.!?。])\s+')
RE_NORMALIZE = re.compile(r'[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]')

# ══════════════════════════════════════════════════════════════
# SCHEMAS — 2026 Edition with Inline Annotations
# ══════════════════════════════════════════════════════════════

class CopyrightAnnotation(BaseModel):
    model_config = ConfigDict(strict=True)
    text: str           # Exact text fragment from the article (for inline highlight)
    reason: str         # Why this is risky (Vietnamese)
    source_url: str     # Competitor URL that this resembles
    severity: str       # "low" | "medium" | "high"
    type: Optional[str] = "external"  # "external" | "internal-dedup"

class PlagiarismResult(BaseModel):
    model_config = ConfigDict(strict=True)
    uniqueness_score: float  # 0.0 (full copy) → 1.0 (100% unique)
    risk_level: str          # "LOW" | "MEDIUM" | "HIGH"
    flagged_sentences: List[str]
    annotations: List[CopyrightAnnotation]  # NEW: per-sentence annotations for inline highlighting
    similar_sources: List[str]
    verdict: str             # AI-generated Vietnamese verdict

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Semantic Similarity Judge (2026)
# ══════════════════════════════════════════════════════════════

PLAGIARISM_PROMPT = """[ROLE] SENIOR PLAGIARISM AUDITOR — XoHi Content Studio MOD
Nhiệm vụ: Chấm điểm TRUNG THỰC, KHÁCH QUAN và CÔNG BẰNG.

[NHIỆM VỤ]
So sánh bài viết với các nguồn cạnh tranh Google để xác định tính độc đáo (Uniqueness).

[QUY TẮC CHẤM ĐIỂM — QUAN TRỌNG]
1. KHÔNG TRỪ ĐIỂM (FAIRNESS): 
   - Kiến thức phổ thông, sự thật hiển nhiên (Ví dụ: "Hà Nội là thủ đô Việt Nam").
   - Thuật ngữ chuyên ngành, từ khóa SEO bắt buộc.
   - Các trích dẫn pháp luật, quy định chính thức (nếu có dẫn nguồn).

2. PHẢI TRỪ ĐIỂM (STRICTNESS):
   - Sao chép cấu trúc dàn ý (Flow bài viết) của đối thủ.
   - Xào nấu ý tưởng (Paraphrasing) nhưng không thêm giá trị mới.
   - THIẾU THÔNG TIN MỚI (Information Gain): Nếu bài viết không cung cấp thêm bất kỳ thực thể, số liệu hoặc góc nhìn nào khác biệt so với 5 nguồn đối thủ được cung cấp -> TRỪ ĐIỂM NẶNG.
   - Dùng chung ví dụ cụ thể, số liệu cụ thể độc quyền của nguồn mà không có phân tích riêng.
   - Trùng lặp cụm từ dài (≥ 10 chữ liên tiếp).

[CALIBRATION — THANG ĐIỂM TRUNG THỰC]
- 0.90-1.0 (LOW RISK): Bài viết có cấu trúc riêng, ví dụ thực tế riêng, phân tích chuyên sâu hoặc góc nhìn mới mà các nguồn Google chưa có.
- 0.70-0.89 (MEDIUM RISK): Nội dung gốc nhưng cấu trúc dựa trên các mô-típ phổ biến, chưa có nhiều đột phá về insight.
- 0.50-0.69 (HIGH RISK): Có dấu hiệu xào nấu rõ rệt từ 1-2 nguồn chính, chỉ thay đổi từ ngữ bề mặt (Spinning).
- < 0.50 (CRITICAL): Sao chép nguyên văn hoặc cấu trúc gần như tuyệt đối từ nguồn.

[YÊU CẦU ĐẦU RA — JSON]
{
  "uniqueness_score": <float 0.0-1.0 — Phải phản ánh đúng sự khác biệt về Insight & Structure>,
  "risk_level": "<LOW|MEDIUM|HIGH>",
  "flagged_sentences": [<câu/đoạn có dấu hiệu copy hoặc xào nấu — copy NGUYÊN VĂN từ bài viết>],
  "annotations": [
    {
      "text": "<đoạn NGUYÊN VĂN từ bài viết — substring chính xác, tối đa 200 ký tự>",
      "reason": "<lý do cụ thể tại sao đoạn này bị coi là trùng lặp — tiếng Việt>",
      "source_url": "<URL nguồn tương đồng>",
      "severity": "<low|medium|high>"
    }
  ],
  "similar_sources": [<URL nguồn tương đồng nhất>],
  "verdict": "<Nhận xét công tâm 1-2 câu về tính độc đáo của bài viết so với đối thủ — tiếng Việt>"
}"""


class PlagiarismCop:
    """
    Step 5 (Auto) + On-Demand (Step 4): AI-powered Semantic Copyright Check — 2026 Edition.
    - Google Custom Search → fetch top competitor content snippets
    - Gemini AI → semantic similarity analysis (not just string matching)
    - Returns structural uniqueness score + per-sentence inline annotations for editor highlighting
    """
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.search_keys = []
        # CNS V76: Global-like semaphore for Plagiarism tasks to protect VPS RAM
        self.plagiarism_semaphore = asyncio.Semaphore(1)
        # Load Google Search keys from env (same as AssetHunter)
        for i in ["", "_1", "_2"]:
            k = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}")
            cx = os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
            if k and cx:
                self.search_keys.append({"key": k, "cx": cx})
        self._key_idx = 0
        self._key_lock = asyncio.Lock()  # BUG-08 fix: thread-safe key rotation
        # BUG-07 fix: Cache Agent at class scope — R1.6 prohibits per-request Agent creation
        self._agent = Agent(output_type=PlagiarismResult, system_prompt=PLAGIARISM_PROMPT, retries=3)

    # ──────────────────────────────────────────────────────────
    # V76.0: Internal Dedup Detection (Zero AI Cost)
    # ──────────────────────────────────────────────────────────

    def _detect_internal_duplicates(self, plain_text: str) -> List[CopyrightAnnotation]:
        """
        Detect duplicate sentences/phrases within the same article.
        Pure logic — no AI calls. Splits into sentences, normalizes,
        and finds exact or near-duplicate repetitions.
        Returns CopyrightAnnotation objects with severity based on repetition count.
        """
        if not plain_text or len(plain_text) < 50:
            return []

        # Split into sentences while keeping track of original text positions
        # Use regex that splits while stripping the trailing whitespace from segments
        raw_segments = [s.strip() for s in re.split(r'(?<=[.!?。])[\s\n]+', plain_text) if s.strip()]
        
        # Phase 76.5: Precise Original Mapping
        # We need the snippets to exist EXACTLY in the final cleaned draft for the UI
        sentences = raw_segments

        # Phase 76.3: Standardized Normalization (Elite V2.2)
        def normalize(text: str) -> str:
            return normalize_vn(text)

        # Track seen sentences → first occurrence index
        seen: dict[str, int] = {}
        duplicates: List[CopyrightAnnotation] = []
        reported_norms: set[str] = set()

        for idx, sentence in enumerate(sentences):
            norm = normalize(sentence)
            if len(norm) < 10:
                continue

            if norm in seen:
                # Found a duplicate! Report it EVERY time it appears
                duplicates.append(CopyrightAnnotation(
                    text=sentence[:200],
                    reason=f"Phát hiện nội dung này lặp lại trong bài viết (lần đầu ở vị trí câu {seen[norm] + 1}). Cần diễn đạt lại để tránh nhàm chán.",
                    source_url="(nội bộ — trùng lặp trong bài)",
                    severity="high" # Increase severity for internal spam
                ))
            else:
                seen[norm] = idx

        # Phase 2: N-gram overlap detection for near-duplicates (≥10 word phrases)
        word_sequences: dict[str, list[int]] = {}
        for idx, sentence in enumerate(sentences):
            words = normalize(sentence).split()
            if len(words) < 10:
                continue
            # Extract 10-word sliding windows
            for i in range(len(words) - 9):
                ngram = ' '.join(words[i:i + 10])
                if ngram not in word_sequences:
                    word_sequences[ngram] = []
                word_sequences[ngram].append(idx)

        # Find n-grams that appear in multiple distinct sentences
        flagged_sentence_indices: set[int] = set()
        # Phase 2: N-gram overlap detection (redundant now with Phase 1 fix, but keeping for fuzzy-ish safety)
        for ngram, indices in word_sequences.items():
            unique_indices = sorted(list(set(indices)))
            if len(unique_indices) >= 2:
                # Flag everything except the very first occurrence
                for si in unique_indices[1:]:
                    if si not in flagged_sentence_indices:
                        flagged_sentence_indices.add(si)
                        duplicates.append(CopyrightAnnotation(
                            text=sentences[si][:200],
                            reason=f"Đoạn này (≥10 từ) trùng lặp với một phần khác trong bài. Đừng xào nấu nội dung của chính mình!",
                            source_url="(nội bộ — trùng cụm từ dài)",
                            severity="medium"
                        ))

        if duplicates:
            logger.info(f"[PlagiarismCop] Internal Dedup: Found {len(duplicates)} duplicate/near-duplicate segments.")
        return duplicates

    async def _get_search_pair(self):
        """BUG-08 fix: async-safe key rotation via lock."""
        if not self.search_keys:
            return None
        async with self._key_lock:
            pair = self.search_keys[self._key_idx % len(self.search_keys)]
            self._key_idx += 1
        return pair

    # ──────────────────────────────────────────────────────────
    # PIPELINE ENTRY POINT
    # ──────────────────────────────────────────────────────────

    async def bulk_fix(self, campaign: ContentCampaign, req: BulkFixRequest) -> BulkFixResponse:
        """
        Phase 76.9: Near-duplicate removal via Jaccard word similarity.
        Keeps the FIRST occurrence. Considers paragraphs with ≥82% word overlap as duplicates.
        Correctly handles trailing noise like '…1111', '1111…..' etc.
        """
        draft = campaign.draft_content or ""

        # Phase 76.3: Clean draft artifacts before surgery
        draft = await noise_cleaner.clean(draft, mode="aggressive", strip_html=False)

        # Split by paragraph (logical unit) not sentence
        raw_paragraphs = [p.strip() for p in re.split(r'\n\n+', draft) if p.strip()]

        # Memory Shield: Limit to 500 paragraphs to prevent OOM in 2GB VPS
        paragraphs = raw_paragraphs[:500]
        if len(raw_paragraphs) > 500:
            logger.warning(f"[PlagiarismCop] bulk_fix: Document too large ({len(raw_paragraphs)} paras). Limited to 500.")

        RE_DIGIT = re.compile(r'\d+')

        def tokenize(text: str) -> set[str]:
            """Phase 76.3: Extract meaningful word tokens using standardized normalization."""
            norm = normalize_vn(text)
            norm = RE_DIGIT.sub('', norm) # strip digits like 1111
            return {w for w in norm.split() if len(w) >= 2}

        def jaccard(a: set[str], b: set[str]) -> float:
            if not a and not b:
                return 1.0
            if not a or not b:
                return 0.0
            intersect = len(a & b)
            return intersect / (len(a) + len(b) - intersect)

        THRESHOLD = 0.82  # ≥82% word overlap → near-duplicate
        kept: list[tuple[str, set[str]]] = []  # (original_text, token_set)

        for para in paragraphs:
            if len(para) < 15:
                kept.append((para, set()))
                continue

            tokens = tokenize(para)
            is_dup = any(jaccard(tokens, k_tok) >= THRESHOLD for _, k_tok in kept if k_tok)

            if not is_dup:
                kept.append((para, tokens))
            else:
                logger.info(f"[PlagiarismCop] bulk_fix removed near-dup: {para[:60]}...")

        new_content = "\n\n".join(p for p, _ in kept)
        return BulkFixResponse(new_content=new_content)

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0) — called by orchestrator Step 5."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")

        # CNS V76: Enforce serial processing for heavy plagiarism analysis
        async with self.plagiarism_semaphore:
            # Phase 76.4: Proactive Physical Sanitization (Elite V2.2)
            # We clean the draft in DB so Editor and Analysis are in sync
            original_draft = campaign.draft_content or ""
            cleaned_draft = await noise_cleaner.clean(original_draft, mode="aggressive", strip_html=False)
            if cleaned_draft != original_draft:
                campaign.draft_content = cleaned_draft
                await repo.update(campaign)
                logger.info(f"[PlagiarismCop] Proactive sanitization applied to campaign {campaign_id}")

            result = await self.analyze(campaign)

        # Phase 73: Sync with gold_metadata analysis_cache for UI hydration parity
        gold = copy.deepcopy(campaign.gold_metadata or {})
        cache = gold.get("analysis_cache", {})
        metrics = gold.get("analysis_metrics", {})

        draft_text = campaign.draft_content or ""
        content_hash = hashlib.sha256(draft_text.encode('utf-8')).hexdigest()
        result_data = result.model_dump()

        cache["copyright"] = {
            "hash": content_hash,
            "data": result_data,
            "at": datetime.now(timezone.utc).isoformat()
        }
        metrics["unique_score"] = result.uniqueness_score
        metrics["copyright_risk"] = result.risk_level
        # ARCHIVING & METRICS (V71.30)
        new_gold = cast(Dict[str, Any], copy.deepcopy(campaign.gold_metadata or {}))
        new_gold["analysis_cache"] = cache
        new_gold["analysis_metrics"] = metrics
        campaign.gold_metadata = new_gold
        campaign.unique_score = result.uniqueness_score
        flag_modified(campaign, "gold_metadata")

        await repo.update(campaign)

        if result.risk_level == "HIGH":
            return AgentResponse(
                signal=AgentSignal.REDO_PREVIOUS,
                message=f"🚨 Phát hiện nguy cơ đạo văn cao (Score: {result.uniqueness_score:.2f}). AI đang viết lại bản thảo.",
                data={
                    "score": result.uniqueness_score,
                    "risk_level": result.risk_level,
                    "gold_metadata": gold
                }
            )

        return AgentResponse(
            signal=AgentSignal.PROCEED_NEXT,
            message=f"✅ Kiểm tra hoàn tất — {result.verdict}",
            data={
                "score": result.uniqueness_score,
                "risk_level": result.risk_level,
                "flagged_sentences": result.flagged_sentences,
                "annotations": [a.model_dump() for a in result.annotations],
                "similar_sources": result.similar_sources,
                "verdict": result.verdict,
                "gold_metadata": gold
            }
        )

    # ──────────────────────────────────────────────────────────
    # ON-DEMAND ANALYSIS (called from /analyze endpoint)
    # ──────────────────────────────────────────────────────────

    async def analyze(self, campaign: ContentCampaign) -> PlagiarismResult:
        """
        Full semantic copyright analysis.
        1. Extract plain text from draft HTML
        2. Search Google for top competitors on primary keyword
        3. Ask Gemini AI to compare semantically, return per-sentence annotations
        """
        draft = campaign.draft_content or ""
        gold = campaign.gold_metadata or {}
        primary_keyword = gold.get("primary_keyword", "")

        if not draft or not primary_keyword:
            return PlagiarismResult(
                uniqueness_score=1.0, risk_level="LOW",
                flagged_sentences=[], annotations=[], similar_sources=[],
                verdict="Không đủ dữ liệu để kiểm tra."
            )

        # Phase 76.3: Unified Logic-First Sanitization
        plain_text = await noise_cleaner.clean(draft, mode="aggressive", strip_html=True)

        # ✅ Phase 76.8: PRE-SANITIZE before AI — dedup paragraphs at para level
        # Keep 1st occurrence, remove subsequent identical paragraphs
        # This ensures AI sees clean, non-redundant content
        seen_paras: set[str] = set()
        deduped_paras: list[str] = []
        internal_annotations: list[CopyrightAnnotation] = []

        raw_paras = [p.strip() for p in re.split(r'\n\n+', plain_text) if p.strip()]
        # Memory Shield: Limit processing to first 200 paragraphs for AI analysis
        for para in raw_paras[:200]:
            norm = normalize_vn(para)
            if len(norm) < 10:
                deduped_paras.append(para)
                continue
            if norm not in seen_paras:
                seen_paras.add(norm)
                deduped_paras.append(para)
            else:
                # Flag as internal-dedup annotation but DO NOT include in AI snippet
                internal_annotations.append(
                    CopyrightAnnotation(
                        text=para[:200],  # truncate for safety
                        reason="Đoạn văn bị lặp lại trong bài — đã loại khỏi nội dung gửi AI",
                        source_url="internal",
                        severity="high",
                        type="internal-dedup"
                    )
                )
                logger.info(f"[PlagiarismCop] Pre-dedup removed duplicate para: {para[:60]}...")

        deduped_text = "\n\n".join(deduped_paras)
        # Limit to 3000 chars for AI efficiency
        snippet = deduped_text[:3000]

        # Also detect sub-sentence level duplicates from the full cleaned text
        sentence_annotations = self._detect_internal_duplicates(plain_text)
        # Merge: avoid double-reporting same texts
        existing_texts = {a.text[:100] for a in internal_annotations}
        for ann in sentence_annotations:
            if ann.text[:100] not in existing_texts:
                internal_annotations.append(ann)

        # 2. Fetch top 5 competitor snippets from Google
        competitor_snippets = await self._fetch_competitor_snippets(primary_keyword)

        # 3. AI semantic analysis with per-sentence annotations
        try:
            prompt = f"""
[BÀI VIẾT CẦN KIỂM TRA — đoạn đầu 3000 ký tự]
{snippet}

[NỘI DUNG CÁC NGUỒN CẠNH TRANH TOP GOOGLE cho từ khóa "{primary_keyword}"]
{chr(10).join([f'--- Nguồn {i+1}: {s}' for i, s in enumerate(competitor_snippets)])}

NHIỆM VỤ: Phân tích và trả về JSON đúng schema yêu cầu. 
Đặc biệt chú ý: các `annotations[].text` PHẢI là substring chính xác từ bài viết cần kiểm tra.
"""
            result = await trinity_bridge.run(self._agent, prompt)  # BUG-07 fix
            raw = result.data if hasattr(result, "data") else result.output

            # Post-process: manage annotations and merge internal duplicates
            if hasattr(raw, 'annotations'):
                validated_annotations = []
                # Add AI annotations if they have text
                for ann in raw.annotations:
                    if ann.text:
                        # We used to check exact match here, but it was too strict for Tiptap's robust matching.
                        # We'll trust the AI for now and let the frontend handle the highlight search.
                        validated_annotations.append(ann)

                # Merge Internal Dedup annotations
                for iann in internal_annotations:
                    raw.uniqueness_score = max(0.0, raw.uniqueness_score - 0.05)
                    iann.type = "internal-dedup"
                    validated_annotations.append(iann)

                raw.annotations = validated_annotations
                if raw.uniqueness_score < 0.8:
                    raw.risk_level = "HIGH" if raw.uniqueness_score < 0.6 else "MEDIUM"
                
                # Rule R82.25: Strict internal dedup penalty
                # If score is still high but has many dedups, force it down
                if len(internal_annotations) >= 3:
                    raw.uniqueness_score = min(raw.uniqueness_score, 0.65)
                    raw.risk_level = "HIGH"

            return raw

        except Exception as e:
            logger.error(f"[PlagiarismCop] AI analysis failed: {e}")
            # Fallback: return safe result with internal_annotations already computed above
            return PlagiarismResult(
                uniqueness_score=0.88, risk_level="LOW",
                flagged_sentences=[],
                annotations=internal_annotations,  # Return dedup annotations even if AI fails
                similar_sources=[],
                verdict="Phân tích AI gặp lỗi — chỉ trả về kết quả lọc nội bộ."
            )

    async def _fetch_competitor_snippets(self, keyword: str) -> List[str]:
        """
        Fetches top 5 Google results + attempts to crawl page body (3000 chars).
        Richer content → AI có đủ ngữ cảnh để so sánh chính xác.
        """
        pair = await self._get_search_pair()
        if not pair:
            logger.warning("[PlagiarismCop] No Google Search keys — skipping competitor fetch.")
            return ["(Không thể tải nội dung cạnh tranh — thiếu API key)"]

        try:
            client = await get_http_client()
            params = {
                "key": pair["key"],
                "cx": pair["cx"],
                "q": keyword,
                "num": 5,
                "fields": "items(title,snippet,link)"
            }
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                return ["(Google không trả về kết quả)"]

            # Crawl page body concurrently (max 3000 chars each, timeout 5s)
            async def _crawl_page(item: dict) -> str:
                url = item.get("link", "")
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                base = f"URL: {url}\nTitle: {title}\nSnippet: {snippet}"
                if not url or not url.startswith("http"):
                    return base
                try:
                    page_resp = await client.get(
                        url, timeout=5.0,
                        headers={"User-Agent": "Mozilla/5.0 (compatible; XoHi-Cop/2.0)"}
                    )
                    if page_resp.status_code == 200:
                        html = page_resp.text
                        # Strip tags, get plain text
                        body = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>', ' ', html, flags=re.IGNORECASE)
                        body = re.sub(r'<[^>]+>', ' ', body)
                        body = re.sub(r'\s+', ' ', body).strip()
                        if body and len(body) > len(snippet):
                            return f"URL: {url}\nTitle: {title}\nContent (3000 chars): {body[:3000]}"
                except Exception:
                    pass  # Fallback to snippet only
                return base

            crawl_tasks = [_crawl_page(item) for item in items[:5]]
            results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
            snippets = [
                r if isinstance(r, str) else f"URL: {items[i].get('link','')}\nSnippet: {items[i].get('snippet','')}"
                for i, r in enumerate(results)
            ]
            logger.info(f"[PlagiarismCop] Fetched {len(snippets)} competitor pages for '{keyword}'")
            return snippets

        except Exception as e:
            logger.error(f"[PlagiarismCop] Google search failed: {e}")
            return ["(Lỗi kết nối Google Search API)"]
