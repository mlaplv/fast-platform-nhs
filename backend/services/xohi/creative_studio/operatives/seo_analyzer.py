import asyncio
import logging
import hashlib
import os
import re
import copy
from typing import List, Dict, Union, Optional
from datetime import datetime, timezone

from pydantic_ai import Agent
from backend.utils.http_client import get_http_client
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.xohi.creative_studio.models.schemas import SeoReport, SeoSignal, SeoAnnotation
from backend.database.repositories import ContentCampaignRepository
from backend.database.models.content import ContentCampaign
from backend.services.event_bus import event_bus

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — AI SEO Judge 2026
# ══════════════════════════════════════════════════════════════

SEO_ANALYSIS_PROMPT = """[ROLE] SENIOR SEO STRATEGIST — XoHi Intelligence 2026
Nhiệm vụ: Chấm điểm SEO TRUNG THỰC và KHÁCH QUAN. Tuyệt đối không nương tay.

[PHƯƠNG PHÁP LUẬN 2026]
Google 2026 ưu tiên bài viết mang lại GIÁ TRỊ THỰC (Information Gain).
- Nếu nội dung chỉ là nhặt nhạnh từ đối thủ mà không có insight khác biệt: ĐIỂM THẤP.
- Nếu không có dữ liệu thực tế hoặc lời khuyên chuyên gia: ĐIỂM THẤP.

[NHIỆM VỤ]
So sánh bài viết với các nguồn TOP GOOGLE được cung cấp để chấm 7 tiêu chí:
1. search_intent_match (20%) — Có giải quyết được nỗi đau/câu hỏi của user tốt hơn đối thủ không?
2. eeat_signals (20%) — Có bằng chứng chuyên gia, kinh nghiệm thực tế không?
3. entity_coverage (15%) — Bao phủ đầy đủ các concept quan trọng so với đối thủ chưa?
4. ai_naturalness (15%) — Văn phong có mượt mà, tránh lặp lại cấu trúc máy móc?
5. featured_snippet_potential (15%) — Cấu trúc câu trả lời có sắc bén để AI trích dẫn?
6. semantic_richness (10%) — Sử dụng thuật ngữ chuyên sâu thay vì từ ngữ phổ thông?
7. technical_seo (5%) — H1/H2/H3 structure, CTA.

[QUY TẮC R2026.9: H1 & TITLE INTEGRITY]
Tuyệt đối KHÔNG đề xuất thay đổi thẻ H1 hoặc Tiêu đề nếu chúng đã chứa từ khóa chính và có cấu trúc tốt. Ưu tiên giữ nguyên bản sắc của bài viết gốc.

[YÊU CẦU ĐẦU RA — JSON]
{
  "total_score": <int 0-100 — Phản ánh chính xác Information Gain so với đối thủ>,
  "grade": "<A|B|C|D|F>",
  "signals": [<7 SeoSignal objects>],
  "summary": "<Nhận xét trung thực 2 câu tiếng Việt — Nêu rõ bài viết đang thua/thắng đối thủ ở điểm nào>",
  "quick_wins": ["<gợi ý 1>", "<gợi ý 2>", "<gợi ý 3>"],
  "seo_annotations": [
    {
      "type": "<missing_h1|missing_h2|keyword_missing|weak_intro|thin_section|ai_stiff|missing_cta|keyword_stuffing>",
      "text": "<CỤM 5-15 TỪ ĐẶC TRƯNG NGUYÊN VĂN từ bài viết — PHẢI tồn tại chính xác trong bài, KHÔNG paraphrase, KHÔNG dùng toàn bộ đoạn>",
      "message": "<lý do và hướng dẫn fix cụ thể — tiếng Việt>",
      "severity": "<info|warning|error>"
    }
  ]
}

[YÊU CẦU BẮT BUỘC]
- Nếu `total_score` < 95: BẮT BUỘC phải có ít nhất 1-3 `seo_annotations` chỉ ra chính xác đoạn nào cần cải thiện hoặc thiếu hụt so với đối thủ.
- Tuyệt đối không để trống `seo_annotations` nếu bài viết không đạt điểm tối đa.

CALIBRATION:
- A (>= 85): Xuất sắc, có insight/dữ liệu độc quyền vượt trội đối thủ (High Information Gain).
- B (>= 70): Tốt, đầy đủ thông tin nhưng insight chưa thực sự đột phá.
- C (>= 55): Đạt yêu cầu kỹ thuật nhưng nội dung còn mỏng và chung chung.
- D/F (< 55): Yếu, xào nấu lộ liễu hoặc thiếu quá nhiều thực thể quan trọng.
"""


class SeoAnalyzer:
    """
    On-Demand SEO Analyzer for Step 4 Content Studio — 2026 Edition.
    Uses Gemini AI to evaluate content against 7 modern ranking signals.
    Returns per-passage seo_annotations for inline editor highlighting.
    """

    # CNS Phase 82.35: Class-Level Resource Shielding (Global Semaphore)
    _seo_semaphore = asyncio.Semaphore(1)
    _key_lock = asyncio.Lock()
    _key_idx = 0

    def __init__(self):
        # Load Google Search keys for competitor fetch
        self.search_keys = []
        for i in ["", "_1", "_2"]:
            k = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}")
            cx = os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
            if k and cx:
                self.search_keys.append({"key": k, "cx": cx})
        self._key_lock = asyncio.Lock()
        
        # BUG-07 fix: Cache Agent at class scope — R1.6 prohibits per-request Agent creation
        self._agent = Agent(output_type=SeoReport, system_prompt=SEO_ANALYSIS_PROMPT, retries=3)

    async def _emit_log(self, campaign: ContentCampaign, msg: str):
        """Emit progress event to the system bus."""
        await event_bus.emit("CONTENT_PROGRESS", {
            "campaign_id": str(campaign.id),
            "user_id": str(campaign.user_id),
            "message": msg,
            "status": "PROCESSING",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def _get_search_pair(self) -> Optional[Dict[str, str]]:
        if not self.search_keys: return None
        async with self._key_lock:
            pair = self.search_keys[self.__class__._key_idx % len(self.search_keys)]
            self.__class__._key_idx += 1
        return pair

    async def _fetch_competitors(self, keyword: str) -> List[str]:
        """Fetch top competitor content for semantic comparison."""
        pair = await self._get_search_pair()
        if not pair: return ["(Không thể tải nội dung cạnh tranh)"]
        try:
            client = await get_http_client()
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": pair["key"],
                    "cx": pair["cx"],
                    "q": keyword,
                    "num": 5
                }
            )
            data = response.json()
            items = data.get("items", [])
            return [f"{item['title']}: {item.get('snippet', '')}" for item in items]
        except Exception as e:
            logger.error(f"[SEO] Search API error: {e}")
            return ["(Lỗi khi kết nối Google Search API)"]

    async def analyze(self, campaign) -> SeoReport:
        """
        Performs full SEO analysis against top 5 competitor snippets.
        CNS Phase 82.35: Enforce GLOBAL serial processing for SEO.
        """
        async with self._seo_semaphore:
            logs = ["🔍 Khởi động SEO Analysis Engine..."]
            await self._emit_log(campaign, logs[-1])
            draft = campaign.draft_content or ""
            # Phase 76.3: Unified Logic-First Sanitization
            # clean_draft keeps HTML for AI structure analysis, pure_text for exact word counts/density
            clean_draft = await noise_cleaner.clean(draft, mode="light", strip_html=False)
            pure_text = await noise_cleaner.clean(draft, mode="light", strip_html=True)

            # Phase 115: Smart topic fallback — extract from H1 or first words of article
            # NEVER use a hardcoded default that could mismatch the actual content
            raw_topic = campaign.get_gold_val("topic")
            if raw_topic:
                topic = raw_topic
            else:
                import re as _re
                # Try H1 first
                h1_match = _re.search(r'<h1[^>]*>(.*?)</h1>', draft, _re.IGNORECASE | _re.DOTALL)
                if h1_match:
                    topic = _re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                else:
                    # Fall back to first 8 words of pure text
                    words = pure_text.split()
                    topic = " ".join(words[:8]) if words else "SEO content"
                logger.info(f"[SEO] No campaign topic set — auto-detected: '{topic}'")
            
            logs.append(f"📡 Đang tải nội dung đối thủ cho: '{topic}'...")
            await self._emit_log(campaign, logs[-1])
            competitors = await self._fetch_competitors(topic)
            competitor_str = "\n".join(competitors)
            
            logs.append("🧠 Đang phân tích SEO bằng Neural Engine...")
            await self._emit_log(campaign, logs[-1])
            # Logic Layer: Pass data to AI judge
            user_input = f"""
[BÀI VIẾT ĐANG CHẤM]
CHỦ ĐỀ: {topic}
DRAFT:
{clean_draft[:8000]}  # CNS V76: Clip for token safety

[ĐỐI THỦ CẠNH TRANH TOP GOOGLE]
{competitor_str}
"""
            # CNS V76: Use ROLE_BRAIN for High-IQ Analysis
            response = await trinity_bridge.run(
                agent=self._agent, 
                prompt=user_input, 
                role="brain"
            )
            report = response.data if hasattr(response, 'data') else response.output
            report.logs = logs
            
            # Phase 73.20: Deterministic Override for Keyword Density (Must use pure_text!)
            primary_kw = campaign.get_gold_val("topic")
            if primary_kw:
                extra_annotations = self._audit_keyword_density(pure_text, primary_kw)
                if hasattr(report, 'seo_annotations'):
                    report.seo_annotations.extend(extra_annotations)
                elif isinstance(report, dict) and 'seo_annotations' in report:
                    report['seo_annotations'].extend(extra_annotations)
            
            return report

    def _audit_keyword_density(self, plain_text: str, primary: str) -> List[SeoAnnotation]:
        """Deterministic safety check for keyword density (Rule R73.25)."""
        annotations = []
        words = plain_text.split()
        total_words = len(words)
        if total_words < 50: return []
        
        count = plain_text.lower().count(primary.lower())
        kw_density = (count / total_words) * 100
        
        if kw_density > 3.0:
            # Find a sentence with keyword stuffing
            sentences = re.split(r'[.!?]', plain_text)
            kw_pattern = re.compile(re.escape(primary.lower()), re.IGNORECASE)
            stuffed = next((s.strip() for s in sentences if len(kw_pattern.findall(s)) >= 3), "")
            annotations.append(SeoAnnotation(
                type="keyword_stuffing",
                text=stuffed[:120] if stuffed else "",
                message=f"🚫 Mật độ từ khóa quá cao ({kw_density:.1f}%) — Google 2026 penalize keyword stuffing. Nên giảm xuống 1-2%.",
                severity="error"
            ))
        elif kw_density < 0.5 and primary:
            annotations.append(SeoAnnotation(
                type="keyword_missing", text="",
                message=f"⚠️ Từ khóa chính '{primary}' xuất hiện quá ít ({kw_density:.1f}%). Nên đặt trong H1, intro paragraph và các H2 chính.",
                severity="warning"
            ))

        return annotations
