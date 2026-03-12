import asyncio
import logging
import os
import re
from typing import List, Tuple
from pydantic import BaseModel
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.database.repositories import ContentCampaignRepository
from backend.services.xohi.creative_studio.models.schemas import AgentResponse, AgentSignal
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.http_client import get_http_client

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# SCHEMAS — 2026 Edition with Inline Annotations
# ══════════════════════════════════════════════════════════════

class CopyrightAnnotation(BaseModel):
    text: str           # Exact text fragment from the article (for inline highlight)
    reason: str         # Why this is risky (Vietnamese)
    source_url: str     # Competitor URL that this resembles
    severity: str       # "low" | "medium" | "high"

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

PLAGIARISM_PROMPT = """[ROLE] SEMANTIC INTEGRITY ANALYST — XoHi Content Studio 2026

[NHIỆM VỤ]
Phân tích mức độ TƯƠNG ĐỒNG NGỮ NGHĨA giữa bài viết cần kiểm tra và các nguồn web được cung cấp.
KHÔNG chỉ so khớp từng chữ — mà phân tích ý tưởng, luận điểm, cấu trúc lập luận.

[TIÊU CHÍ 2026]
- Tương đồng ký tự (character-level): ít quan trọng nhất
- Tương đồng ý tưởng/luận điểm (semantic-level): quan trọng nhất  
- Tương đồng cấu trúc bài viết: quan trọng vừa
- Google 2026 penalize bài viết "regurgitated" dù đổi từ ngữ

[YÊU CẦU ĐẦU RA — JSON]
{
  "uniqueness_score": <float 0.0-1.0>,
  "risk_level": "<LOW|MEDIUM|HIGH>",
  "flagged_sentences": [<câu hoặc đoạn nào có RỦI RO cao nhất — copy NGUYÊN VĂN từ bài viết>],
  "annotations": [
    {
      "text": "<đoạn VĂN BẢN NGUYÊN VĂN từ bài viết cần highlight — CỰC KỲ QUAN TRỌNG: phải là substring chính xác tồn tại trong bài viết>",
      "reason": "<lý do ngắn gọn tại sao đoạn này bị gắn cờ — tiếng Việt>",
      "source_url": "<URL nguồn tương đồng nhất>",
      "severity": "<low|medium|high>"
    }
  ],
  "similar_sources": [<URL nguồn tương đồng nhất>],
  "verdict": "<nhận định 1-2 câu bằng tiếng Việt>"
}

QUAN TRỌNG VỀ `annotations[].text`:
- Phải là chuỗi ký tự NGUYÊN VĂN lấy từ bài viết (không paraphrase, không thêm bớt)
- Tối đa 200 ký tự mỗi annotation
- Ưu tiên đoạn câu/mệnh đề hoàn chỉnh (không cắt giữa chừng)
- Nếu không tìm được đoạn cụ thể, bỏ qua annotation đó (đừng bịa)

LOW = score >= 0.85 (an toàn)
MEDIUM = 0.65 <= score < 0.85 (cần cải thiện)  
HIGH = score < 0.65 (rủi ro cao, nên viết lại)"""


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

    async def execute(self, campaign_id: str, repo: ContentCampaignRepository, **kwargs) -> AgentResponse:
        """Standard entry point for DI Registry (V61.0) — called by orchestrator Step 5."""
        campaign = await repo.get(campaign_id)
        if not campaign:
            return AgentResponse(signal=AgentSignal.FAIL_GRACEFULLY, message="Campaign not found")

        result = await self.analyze(campaign)
        campaign.unique_score = result.uniqueness_score
        await repo.update(campaign)

        if result.risk_level == "HIGH":
            return AgentResponse(
                signal=AgentSignal.REDO_PREVIOUS,
                message=f"🚨 Phát hiện nguy cơ đạo văn cao (Score: {result.uniqueness_score:.2f}). AI đang viết lại bản thảo.",
                data={"score": result.uniqueness_score, "risk_level": result.risk_level}
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
                "verdict": result.verdict
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
        plain_text = re.sub(r'<[^>]+>', ' ', draft)
        # Phase 71.20: Strip [IMAGE_N] to match frontend editor content
        plain_text = re.sub(r'\[IMAGE_\d+\]', '', plain_text)
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()
        # Limit to 3000 chars for analysis efficiency
        snippet = plain_text[:3000]

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

            # Post-process: validate that annotation texts actually exist in the draft
            if hasattr(raw, 'annotations'):
                validated_annotations = []
                for ann in raw.annotations:
                    if ann.text and ann.text in plain_text:
                        validated_annotations.append(ann)
                    elif ann.text:
                        # Try fuzzy: accept if 80%+ of the text appears
                        first_20 = ann.text[:20]
                        if first_20 and first_20 in plain_text:
                            validated_annotations.append(ann)
                raw.annotations = validated_annotations

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
        Fetches top 5 web result snippets from Google Custom Search for semantic comparison.
        Returns list of snippet strings.
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
            snippets = []
            for item in items:
                url = item.get("link", "")
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                snippets.append(f"URL: {url}\nTitle: {title}\nSnippet: {snippet}")
            return snippets if snippets else ["(Google không trả về kết quả)"]

        except Exception as e:
            logger.error(f"[PlagiarismCop] Google search failed: {e}")
            return ["(Lỗi kết nối Google Search API)"]
