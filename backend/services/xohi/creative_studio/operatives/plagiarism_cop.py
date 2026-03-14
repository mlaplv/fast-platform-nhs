import asyncio
import logging
import os
import re
import copy
import hashlib
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Union, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from sqlalchemy.orm.attributes import flag_modified
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.http_client import get_http_client

logger = logging.getLogger("api-gateway")

# Pre-compiled Regex for Performance (V76.3)
RE_HTML_TAGS = re.compile(r'<[^>]+>')
RE_IMAGE_PLACEHOLDERS = re.compile(r'\[IMAGE_\d+\]')
RE_WHITESPACE = re.compile(r'\s+')
RE_SENTENCE_SPLIT = re.compile(r'(?<=[.!?。])\s+')
RE_NORMALIZE = re.compile(r'[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]')

# ══════════════════════════════════════════════════════════════
# SCHEMAS — 2026 Edition with Inline Annotations
# ══════════════════════════════════════════════════════════════

class CopyrightAnnotation(BaseModel):
    text: str           # Exact text fragment from the article (for inline highlight)
    reason: str         # Why this is risky (Vietnamese)
    source_url: str     # Competitor URL that this resembles
    severity: str       # "low" | "medium" | "high"
    type: Optional[str] = "external"  # "external" | "internal-dedup"

class PlagiarismResult(BaseModel):
    uniqueness_score: float  # 0.0 (full copy) → 1.0 (100% unique)
    risk_level: str          # "LOW" | "MEDIUM" | "HIGH"
    flagged_sentences: List[str]
    annotations: List[CopyrightAnnotation]  # NEW: per-sentence annotations for inline highlighting
    similar_sources: List[str]
    verdict: str             # AI-generated Vietnamese verdict

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Semantic Similarity Judge (2026)
# ══════════════════════════════════════════════════════════════

PLAGIARISM_PROMPT = """[ROLE] SENIOR PLAGIARISM AUDITOR — XoHi Content Studio 2026
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

        # Split into sentences (Vietnamese + English punctuation)
        sentences = RE_SENTENCE_SPLIT.split(plain_text)
        # Filter out very short "sentences" (less than 15 chars are likely fragments)
        sentences = [s.strip() for s in sentences if len(s.strip()) >= 15]

        if len(sentences) < 2:
            return []

        # Normalize for comparison (lowercase, collapse whitespace, strip punctuation)
        def normalize(text: str) -> str:
            text = text.lower().strip()
            text = RE_NORMALIZE.sub('', text)
            text = RE_WHITESPACE.sub(' ', text)
            return text

        # Track seen sentences → first occurrence index
        seen: dict[str, int] = {}
        duplicates: List[CopyrightAnnotation] = []
        reported_norms: set[str] = set()

        for idx, sentence in enumerate(sentences):
            norm = normalize(sentence)
            if len(norm) < 10:
                continue

            if norm in seen and norm not in reported_norms:
                # Found a duplicate!
                reported_norms.add(norm)
                duplicates.append(CopyrightAnnotation(
                    text=sentence[:200],  # Max 200 chars as per prompt schema
                    reason=f"Câu này xuất hiện ít nhất 2 lần trong bài viết (lần đầu ở vị trí {seen[norm] + 1}, lặp lại ở vị trí {idx + 1}). Trùng lặp nội bộ làm giảm chất lượng nội dung.",
                    source_url="(nội bộ — trùng lặp trong cùng bài viết)",
                    severity="medium"
                ))
            elif norm not in seen:
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
        for ngram, indices in word_sequences.items():
            unique_indices = list(set(indices))
            if len(unique_indices) >= 2:
                for si in unique_indices:
                    if si not in flagged_sentence_indices:
                        norm_s = normalize(sentences[si])
                        if norm_s not in reported_norms:
                            flagged_sentence_indices.add(si)
                            reported_norms.add(norm_s)
                            duplicates.append(CopyrightAnnotation(
                                text=sentences[si][:200],
                                reason=f"Cụm ≥10 từ liên tiếp trong câu này trùng lặp với câu khác trong bài. Cần viết lại để đảm bảo nội dung không bị lặp.",
                                source_url="(nội bộ — trùng cụm từ dài)",
                                severity="low" if len(unique_indices) == 2 else "high"
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

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs: object) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0) — called by orchestrator Step 5."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")

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
        metrics["last_analyzed"] = datetime.now(timezone.utc).isoformat()

        gold["analysis_cache"] = cache
        gold["analysis_metrics"] = metrics
        campaign.gold_metadata = gold
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

        # 1. Extract readable text from HTML
        plain_text = RE_HTML_TAGS.sub(' ', draft)
        # Phase 71.20: Strip [IMAGE_N] to match frontend editor content
        plain_text = RE_IMAGE_PLACEHOLDERS.sub('', plain_text)
        plain_text = RE_WHITESPACE.sub(' ', plain_text).strip()
        # Limit to 3000 chars for analysis efficiency
        snippet = plain_text[:3000]

        # 2. Fetch top 5 competitor snippets from Google
        competitor_snippets = await self._fetch_competitor_snippets(primary_keyword)

        # 3. AI semantic analysis with per-sentence annotations
        try:
            # V76.0: Run Internal Dedup concurrently (Zero cost)
            internal_annotations = self._detect_internal_duplicates(plain_text)

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

            # Post-process: validate annotations and merge internal duplicates
            if hasattr(raw, 'annotations'):
                validated_annotations = []
                # Add AI annotations if they exist in text
                for ann in raw.annotations:
                    if ann.text and ann.text in plain_text:
                        validated_annotations.append(ann)
                    elif ann.text:
                        first_20 = ann.text[:20]
                        if first_20 and first_20 in plain_text:
                            validated_annotations.append(ann)
                
                # Merge Internal Dedup annotations (they are already from plain_text)
                for iann in internal_annotations:
                    # Update uniqueness score based on internal dedup
                    raw.uniqueness_score = max(0.0, raw.uniqueness_score - 0.05) # Small penalty per lặp
                    # Add to list with internal type
                    iann.type = "internal-dedup"
                    validated_annotations.append(iann)

                raw.annotations = validated_annotations
                if raw.uniqueness_score < 0.8:
                    raw.risk_level = "HIGH" if raw.uniqueness_score < 0.6 else "MEDIUM"

            return raw

        except Exception as e:
            logger.error(f"[PlagiarismCop] AI analysis failed: {e}")
            # Fallback: return safe default if AI fails
            return PlagiarismResult(
                uniqueness_score=0.88, risk_level="LOW",
                flagged_sentences=[],
                annotations=[],
                similar_sources=[s.get("url", "") for s in competitor_snippets[:3]] if competitor_snippets and isinstance(competitor_snippets[0], dict) else [],
                verdict="Phân tích tự động gặp lỗi — dữ liệu ước tính an toàn."
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
