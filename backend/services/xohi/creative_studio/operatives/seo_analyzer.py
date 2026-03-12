import re
import logging
from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

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

[BỐI CẢNH]
Bạn là chuyên gia SEO hàng đầu 2026, am hiểu sâu về:
- Google Helpful Content System (HCU)
- E-E-A-T framework (Experience, Expertise, Authoritativeness, Trustworthiness)
- Semantic SEO & Entity-based ranking
- AI-Generated Content Detection & Naturalness
- Featured Snippets & Position Zero optimization
- Core Web Vitals & UX signals

[NHIỆM VỤ]
1. Chấm điểm SEO bài viết theo 7 tiêu chí 2026.
2. Tạo danh sách `seo_annotations` — mỗi annotation là một ĐOẠN VĂN NGUYÊN VĂN cụ thể cần cải thiện.

[7 TIÊU CHÍ VÀ TRỌNG SỐ]
1. search_intent_match (20%) — Nội dung có đáp ứng đúng INTENT tìm kiếm không?
2. eeat_signals (20%) — Dấu hiệu E-E-A-T: kinh nghiệm thực tế, chuyên môn, uy tín?
3. entity_coverage (15%) — Bao phủ các thực thể, khái niệm liên quan đủ sâu chưa?
4. ai_naturalness (15%) — Nội dung có tự nhiên, không bị "AI cứng nhắc" không?
5. featured_snippet_potential (15%) — Cấu trúc có phù hợp cho Featured Snippet/PAA không?
6. semantic_richness (10%) — Từ vựng đa dạng, tránh keyword stuffing?
7. technical_seo (5%) — H1/H2/H3 structure, keyword trong heading, CTA rõ ràng?

[ĐẦU RA — JSON CHÍNH XÁC]
{
  "total_score": <int 0-100>,
  "grade": "<A|B|C|D|F>",
  "signals": [<7 SeoSignal objects>],
  "summary": "<2 câu nhận xét tổng quan tiếng Việt>",
  "quick_wins": ["<gợi ý 1>", "<gợi ý 2>", "<gợi ý 3>"],
  "seo_annotations": [
    {
      "type": "<missing_h1|missing_h2|keyword_missing|weak_intro|thin_section|ai_stiff|missing_cta|keyword_stuffing>",
      "text": "<ĐOẠN VĂN NGUYÊN VĂN từ bài viết — phải là substring chính xác>",
      "message": "<lý do và gợi ý cải thiện — tiếng Việt ngắn gọn>",
      "severity": "<info|warning|error>"
    }
  ]
}

QUY TẮC VỀ `seo_annotations[].text`:
- PHẢI là chuỗi ký tự NGUYÊN VĂN lấy từ bài viết (không paraphrase)
- Tối đa 150 ký tự mỗi annotation
- Ưu tiên đoạn câu/cụm từ hoàn chỉnh
- Nếu vấn đề là cấu trúc (thiếu H1, thiếu CTA), `text` là "" (chuỗi rỗng)
- Tối đa 10 annotations, ưu tiên severity "error" trước

ĐIỂM GRADE:
- A: >= 85 | B: >= 70 | C: >= 55 | D: >= 40 | F: < 40

QUAN TRỌNG: Chỉ trả JSON. Không giải thích thêm."""


class SeoAnalyzer:
    """
    On-Demand SEO Analyzer for Step 4 Content Studio — 2026 Edition.
    Uses Gemini AI to evaluate content against 7 modern ranking signals.
    Returns per-passage seo_annotations for inline editor highlighting.
    """

    def __init__(self):
        # BUG-07 fix: Cache Agent at class scope — R1.6 prohibits per-request Agent creation
        self._agent = Agent(output_type=SeoReport, system_prompt=SEO_ANALYSIS_PROMPT, retries=3)

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

        # Extract first 200 chars of each paragraph for the AI to reference
        paragraphs = [p.strip() for p in re.split(r'\n|\r|<p[^>]*>|<\/p>', draft) if len(p.strip()) > 30]
        paragraph_samples = "\n".join([f"[Para {i+1}]: {p[:200]}" for i, p in enumerate(paragraphs[:15])])

        prompt = f"""
[THÔNG TIN BÀI VIẾT]
Tiêu đề: {title}
Từ khóa CHÍNH: {primary}
Từ khóa PHỤ: {', '.join(secondary[:10])}
Phong cách (Persona): {persona}

[DÀN Ý ĐÃ ĐƯỢC PHÊ DUYỆT]
{outline_summary or "(Không có dàn ý)"}

[THỐNG KÊ KỸ THUẬT]
- Số từ: {word_count}
- H1: {h1_count} | H2: {h2_count} | H3: {h3_count}
- Hình ảnh: {img_count}
- Có CTA: {"Có" if has_cta else "Không"}
- Mật độ từ khóa chính: {kw_density}% ({kw_count} lần / {word_count} từ)

[NỘI DUNG BÀI VIẾT — 4000 ký tự đầu]
{plain_text[:4000]}

[CÁC ĐOẠN VĂN (để tạo annotations chính xác)]
{paragraph_samples}

NHIỆM VỤ: Phân tích và chấm điểm theo 7 tiêu chí.
Tạo `seo_annotations` với `text` là NGUYÊN VĂN từ [NỘI DUNG BÀI VIẾT] hoặc [CÁC ĐOẠN VĂN] ở trên.
Trả về JSON theo đúng schema yêu cầu.
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
