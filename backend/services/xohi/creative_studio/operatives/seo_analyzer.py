import os
import asyncio
import logging
import re
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.http_client import get_http_client

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# SCHEMAS — 2026 SEO Signals with Inline Annotations
# ══════════════════════════════════════════════════════════════

class SeoSignal(BaseModel):
    label: str
    score: int           # 0-100
    verdict: str         # Short explanation in Vietnamese
    suggestions: List[str]

class SeoAnnotation(BaseModel):
    type: str      # "missing_h1" | "missing_h2" | "keyword_missing" | "weak_intro" | "thin_section" | "ai_stiff" | "missing_cta" | "keyword_stuffing"
    text: str      # Exact text fragment from the article to highlight (substring), can be "" for structural issues
    message: str   # Vietnamese tip shown in tooltip
    severity: str  # "info" | "warning" | "error"

class SeoReport(BaseModel):
    total_score: int     # 0-100 weighted average
    grade: str           # "A" | "B" | "C" | "D" | "F"
    signals: List[SeoSignal]
    summary: str         # 1-2 line Vietnamese overall verdict
    quick_wins: List[str]    # Top 3 actionable improvements
    seo_annotations: List[SeoAnnotation]  # NEW: per-passage inline annotations for editor

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
      "text": "<ĐOẠN VĂN NGUYÊN VĂN từ bài viết>",
      "message": "<lý do và hướng dẫn fix cụ thể — tiếng Việt>",
      "severity": "<info|warning|error>"
    }
  ]
}

CALIBRATION:
- A (>= 85): Xuất sắc, có insight/dữ liệu độc quyền vượt trội đối thủ.
- B (>= 70): Tốt, đầy đủ thông tin nhưng insight chưa thực sự đột phá.
- C (>= 55): Đạt yêu cầu kỹ thuật nhưng nội dung còn mỏng và chung chung.
- D/F (< 55): Yếu, xào nấu lộ liễu hoặc thiếu quá nhiều thực thể quan trọng."""


class SeoAnalyzer:
    """
    On-Demand SEO Analyzer for Step 4 Content Studio — 2026 Edition.
    Uses Gemini AI to evaluate content against 7 modern ranking signals.
    Returns per-passage seo_annotations for inline editor highlighting.
    """

    def __init__(self):
        # Load Google Search keys for competitor fetch
        self.search_keys = []
        for i in ["", "_1", "_2"]:
            k = os.getenv(f"GOOGLE_SEARCH_API_KEY{i}")
            cx = os.getenv(f"GOOGLE_SEARCH_ENGINE_ID{i}")
            if k and cx:
                self.search_keys.append({"key": k, "cx": cx})
        self._key_idx = 0
        self._key_lock = asyncio.Lock()
        
        # BUG-07 fix: Cache Agent at class scope — R1.6 prohibits per-request Agent creation
        self._agent = Agent(output_type=SeoReport, system_prompt=SEO_ANALYSIS_PROMPT, retries=3)

    async def _get_search_pair(self):
        if not self.search_keys: return None
        async with self._key_lock:
            pair = self.search_keys[self._key_idx % len(self.search_keys)]
            self._key_idx += 1
        return pair

    async def _fetch_competitors(self, keyword: str) -> List[str]:
        """Fetch top competitor content for semantic comparison."""
        pair = await self._get_search_pair()
        if not pair: return ["(Không thể tải nội dung cạnh tranh)"]
        try:
            client = await get_http_client()
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": pair["key"], "cx": pair["cx"], "q": keyword, "num": 5}
            )
            items = response.json().get("items", [])
            async def _crawl(item):
                url = item.get("link", "")
                try:
                    p_resp = await client.get(url, timeout=5.0)
                    if p_resp.status_code == 200:
                        body = re.sub(r'<(script|style)[^>]*>[\s\S]*?</\1>|<[^>]+>', ' ', p_resp.text, flags=re.IGNORECASE)
                        return f"URL: {url}\nContent: {re.sub(r'\s+', ' ', body)[:3000]}"
                except: pass
                return f"URL: {url}\nSnippet: {item.get('snippet', '')}"
            
            return await asyncio.gather(*[_crawl(i) for i in items[:5]])
        except Exception as e:
            logger.error(f"SEO Search failed: {e}")
            return ["(Lỗi kết nối Google Search API)"]

    async def analyze(self, campaign: ContentCampaign) -> SeoReport:
        """
        Performs full AI-powered SEO analysis on draft content.
        """
        draft = campaign.draft_content or ""
        gold = campaign.gold_metadata or {}
        outline = campaign.outline_data or {}

        primary = gold.get("primary_keyword", "")
        secondary = gold.get("secondary_keywords", [])
        title = gold.get("title", "")
        persona = gold.get("persona", "")

        # Extract readable text
        plain_text = re.sub(r'<[^>]+>', ' ', draft)
        # Phase 71.20: Strip [IMAGE_N] to match frontend editor content
        plain_text = re.sub(r'\[IMAGE_\d+\]', '', plain_text)
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()
        word_count = len(plain_text.split())

        # Build technical stats (rule-based, fast)
        h1_count = len(re.findall(r'<h1[^>]*>', draft, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>', draft, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>', draft, re.IGNORECASE))
        img_count = len(re.findall(r'<img[^>]*>', draft, re.IGNORECASE))
        has_cta = bool(re.search(r'class=["\']cta', draft, re.IGNORECASE) or
                       re.search(r'<section[^>]*cta', draft, re.IGNORECASE))

        # Primary keyword frequency
        kw_count = len(re.findall(re.escape(primary.lower()), plain_text.lower())) if primary else 0
        kw_density = round((kw_count / word_count) * 100, 2) if word_count > 0 else 0

        # Build outline summary
        sections = outline.get("sections", [])
        outline_summary = "\n".join([f"- {s.get('heading', '')}" for s in sections[:8]])

        # 1. Fetch competitors for information gain analysis
        competitor_content = await self._fetch_competitors(primary)

        # 2. Extract first 200 chars of each paragraph for the AI to reference
        paragraphs = [p.strip() for p in re.split(r'\n|\r|<p[^>]*>|<\/p>', draft) if len(p.strip()) > 30]
        paragraph_samples = "\n".join([f"[Para {i+1}]: {p[:200]}" for i, p in enumerate(paragraphs[:15])])

        prompt = f"""
[BÀI VIẾT CỦA BẠN — 4000 ký tự đầu]
{plain_text[:4000]}

[NỘI DUNG ĐỐI THỦ TOP GOOGLE cho từ khóa "{primary}"]
{chr(10).join([f'--- Nguồn {i+1}: {s}' for i, s in enumerate(competitor_content)])}

[THÔNG TIN BỔ SUNG]
Tiêu đề: {title}
Từ khóa PHỤ: {', '.join(secondary[:10])}
Persona: {persona}

[DÀN Ý ĐÃ CHỌN]
{outline_summary or "(Không có dàn ý)"}

[THỐNG KÊ KỸ THUẬT]
- Số từ: {word_count} | H1: {h1_count} | H2: {h2_count} | H3: {h3_count}
- CTA: {"Có" if has_cta else "Không"} | Mật độ KW: {kw_density}%

NHIỆM VỤ: Hãy so sánh bài viết của tôi với nội dung đối thủ.
1. Chấm điểm trung thực. Nếu bài tôi nghèo nàn hơn đối thủ về thông tin, hãy cho điểm THẤP.
2. Tạo `seo_annotations` chỉ dẫn chính xác đoạn nào cần thêm insight/dữ liệu hoặc sửa cấu trúc.
"""

        try:
            result = await trinity_bridge.run(self._agent, prompt)
            raw = result.data if hasattr(result, "data") else result.output

            # Post-process: validate annotations reference real text
            if hasattr(raw, 'seo_annotations'):
                validated = []
                for ann in raw.seo_annotations:
                    if not ann.text:  # Structural issues (empty text) are always valid
                        validated.append(ann)
                    elif ann.text in plain_text:
                        validated.append(ann)
                    else:
                        # Accept partial match (first 15 chars)
                        first_15 = ann.text[:15]
                        if first_15 and first_15 in plain_text:
                            validated.append(ann)
                raw.seo_annotations = validated

            # Add rule-based structural annotations (always accurate, no hallucination risk)
            structural_annotations = self._build_structural_annotations(
                draft, plain_text, primary, h1_count, h2_count, h3_count, has_cta, kw_density
            )
            if hasattr(raw, 'seo_annotations'):
                raw.seo_annotations = structural_annotations + raw.seo_annotations

            return raw

        except Exception as e:
            logger.error(f"[SeoAnalyzer] AI analysis failed: {e}")
            # Graceful fallback with rule-based estimate
            tech_score = min(100, int(
                (30 if h1_count == 1 else 5) +
                (20 if h2_count >= 3 else h2_count * 5) +
                (15 if word_count >= 1000 else int(word_count / 100 * 15)) +
                (10 if img_count > 0 else 0) +
                (10 if has_cta else 0) +
                (15 if 1.0 <= kw_density <= 2.5 else max(0, 15 - abs(kw_density - 1.8) * 5))
            ))
            structural_annotations = self._build_structural_annotations(
                draft, plain_text, primary, h1_count, h2_count, h3_count, has_cta, kw_density
            )
            return SeoReport(
                total_score=tech_score,
                grade="B" if tech_score >= 70 else "C" if tech_score >= 55 else "D",
                signals=[
                    SeoSignal(label="technical_seo", score=tech_score,
                              verdict="Phân tích nhanh dựa trên cấu trúc HTML",
                              suggestions=[] if tech_score >= 70 else ["Thêm H2/H3 subheadings", "Kiểm tra CTA"])
                ],
                summary=f"Phân tích AI gặp lỗi. Điểm kỹ thuật ước tính: {tech_score}/100.",
                quick_wins=["Thêm nhiều H2/H3 subheadings rõ ràng", "Đảm bảo keyword chính trong thẻ H1", "Thêm CTA cuối bài"],
                seo_annotations=structural_annotations
            )

    def _build_structural_annotations(
        self, draft: str, plain_text: str, primary: str,
        h1_count: int, h2_count: int, h3_count: int, has_cta: bool, kw_density: float
    ) -> List[SeoAnnotation]:
        """
        Rule-based structural annotations that are always accurate.
        These catch definitive issues: missing H1, missing CTA, keyword stuffing, etc.
        """
        annotations = []

        if h1_count == 0:
            annotations.append(SeoAnnotation(
                type="missing_h1", text="",
                message="❌ Bài viết thiếu thẻ H1 — Google cần H1 để xác định chủ đề chính. Thêm ngay tiêu đề H1 chứa từ khóa chính.",
                severity="error"
            ))
        elif h1_count > 1:
            annotations.append(SeoAnnotation(
                type="missing_h1", text="",
                message=f"⚠️ Bài viết có {h1_count} thẻ H1 — chỉ nên có đúng 1 H1 duy nhất.",
                severity="warning"
            ))

        if h2_count < 2:
            annotations.append(SeoAnnotation(
                type="missing_h2", text="",
                message=f"⚠️ Chỉ có {h2_count} thẻ H2 — nên có ít nhất 3-5 H2 để phân cấp nội dung rõ ràng, giúp Google hiểu cấu trúc bài.",
                severity="warning" if h2_count > 0 else "error"
            ))

        if not has_cta:
            # Try to find the last paragraph to annotate
            last_para_match = re.findall(r'[^.!?]+[.!?]', plain_text[-500:])
            last_sentence = last_para_match[-1].strip() if last_para_match else ""
            annotations.append(SeoAnnotation(
                type="missing_cta", text=last_sentence[:120] if last_sentence else "",
                message="⚠️ Bài viết thiếu CTA (Call-to-Action). Thêm lời kêu gọi hành động cuối bài để tăng conversion và dwell time.",
                severity="warning"
            ))

        if kw_density > 3.0 and primary:
            # Find a sentence with keyword stuffing
            sentences = re.split(r'[.!?]', plain_text)
            stuffed = next((s.strip() for s in sentences if s.lower().count(primary.lower()) >= 3), "")
            annotations.append(SeoAnnotation(
                type="keyword_stuffing",
                text=stuffed[:120] if stuffed else "",
                message=f"🚫 Mật độ từ khóa quá cao ({kw_density}%) — Google 2026 penalize keyword stuffing. Nên giảm xuống 1-2%.",
                severity="error"
            ))
        elif kw_density < 0.5 and primary:
            annotations.append(SeoAnnotation(
                type="keyword_missing", text="",
                message=f"⚠️ Từ khóa chính '{primary}' xuất hiện quá ít ({kw_density}%). Nên đặt trong H1, intro paragraph và các H2 chính.",
                severity="warning"
            ))

        return annotations
