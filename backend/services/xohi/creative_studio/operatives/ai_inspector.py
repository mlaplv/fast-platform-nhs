import re
import asyncio
import logging
from typing import List, Dict, Union, Optional, cast
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.xohi.creative_studio.models.schemas import (
    AiReadyReport, AutoFixResponse, BulkFixResponse, BulkFixRequest,
    GoldMetadata, AiAnnotation
)

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — VIRAL EDGE Algorithm (8 Criteria)
# ══════════════════════════════════════════════════════════════

GEO_ANALYSIS_PROMPT = """[ROLE] VIRAL EDGE CHIEF AUDITOR — XoHi Content Intelligence
Bạn là bộ não đánh giá nội dung tiên tiến nhất. Nhiệm vụ tối thượng: xác định bài viết có xứng đáng TOP 1 Google, lọt AI Overview, và được Perplexity/ChatGPT/Gemini trích dẫn hay không.

[8 TIÊU CHÍ CHỐT HẠ — VIRAL EDGE ALGORITHM]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. search_intent (15%) — SEARCH INTENT MATCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Bài viết có giải quyết CHÍNH XÁC nỗi đau/câu hỏi mà user gõ vào Google không?
- Nếu intent là Informational: phải có câu trả lời trực tiếp trong 100 từ đầu.
- Nếu intent là Transactional: phải có CTA rõ ràng và bảng so sánh.
- Nếu intent là Navigational: phải có thông tin chính xác về thương hiệu/sản phẩm.
→ annotation type: "search_intent" (severity: high nếu lệch intent)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. eeat_authority (15%) — E-E-A-T SIGNALS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Experience: Có trải nghiệm thực tế/case study cụ thể không?
- Expertise: Có thuật ngữ chuyên ngành, phân tích chuyên sâu không?
- Authority: Có trích dẫn nguồn uy tín (báo cáo, chuyên gia, cơ quan) không?
- Trust: Có số liệu kiểm chứng được, không bịa đặt không?
- BẮT BUỘC ≥2 tín hiệu E-E-A-T rõ ràng cho bài viết đạt > 70 điểm.
→ annotation type: "eeat_missing" (severity: high)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. information_gain (15%) — INFORMATION GAIN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Bài viết có mang lại THÔNG TIN MỚI mà đối thủ Top 5 chưa có không?
- Insight độc quyền, góc nhìn khác biệt, dữ liệu riêng → ĐIỂM CAO.
- Chỉ xào nấu lại ý tưởng của đối thủ → TRỪ ĐIỂM NẶNG.
- Thiếu entity/concept quan trọng mà đối thủ đã phủ → TRỪ ĐIỂM.
→ annotation type: "geo_stats" (severity: high nếu thiếu data mới)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. ai_overview_ready (15%) — GOOGLE AI OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Google AI Overview ưu tiên trích xuất từ bài viết có:
- Định nghĩa rõ ràng ngay đầu section (pattern: "X là..." hoặc "X được hiểu là...")
- Bảng tóm tắt (table) hoặc bullet list cho các điểm chính
- Câu trả lời trực tiếp ≤50 từ cho câu hỏi chính của bài
- Format hỏi-đáp (Q&A) cho các sub-section
- Nếu THIẾU các pattern trên → bài viết SẼ KHÔNG được chọn vào AI Overview.
→ annotation type: "ai_overview" (severity: high nếu thiếu cấu trúc)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. featured_snippet (10%) — FEATURED SNIPPET POTENTIAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Có đoạn "direct answer" súc tích ≤40 từ ngay sau H2 không?
- Có numbered list hoặc bullet list rõ ràng cho "top X", "cách làm" không?
- Có bảng so sánh (table) cho câu hỏi "so sánh A vs B" không?
- Cấu trúc H2 có match với câu hỏi thực tế mà user gõ không?
→ annotation type: "snippet_ready" (severity: warning)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. entity_density (10%) — NLP ENTITY COVERAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Mật độ entity đặc trưng: tên riêng, địa danh, con số, thuật ngữ chuyên ngành.
- Tối thiểu 1 entity có giá trị cho mỗi 200 từ.
- Tuyệt đối KHÔNG chấp nhận cụm từ chung chung: "rất nhiều", "phổ biến", "đáng kể", "ngày càng".
- Mỗi entity chung chung tìm được: ghi nhận annotation để fix.
→ annotation type: "entity_gap" (severity: warning)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
7. fluff_penalty (10%) — FLUFF ELIMINATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Mật độ thông tin hữu ích phải đạt trên 75%.
- Mỗi câu "dẫn dắt thừa", "làm màu", "sáo rỗng" → TRỪ 3 ĐIỂM.
- Pattern sáo rỗng: "Trong thời đại 4.0...", "Không thể phủ nhận...", "Như chúng ta đều biết..."
- Lặp lại ý → TRỪ ĐIỂM NẶNG.
→ annotation type: "geo_fluff" (severity: warning/high)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8. citation_pattern (10%) — AI SEARCH CITATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Perplexity/ChatGPT/Gemini ưu tiên trích dẫn bài viết có:
- Câu tóm tắt mạnh mẽ đầu mỗi section (Topic Sentence)
- Số liệu cụ thể kèm ngữ cảnh ("Theo báo cáo X năm 2024, tỷ lệ Y đạt Z%")
- Trích dẫn chuyên gia có tên + chức danh
- Câu kết luận súc tích cuối mỗi section
- Nếu KHÔNG có pattern nào → AI Search sẽ bỏ qua bài viết.
→ annotation type: "citation_weak" (severity: warning)

[YÊU CẦU ĐẦU RA — JSON]
{
  "geo_score": <int 0-100 — Tổng hợp từ 8 tiêu chí, trọng số như trên>,
  "summary": "<Nhận xét chốt hạ 2 câu: bài viết MẠNH nhất ở đâu, YẾU nhất ở đâu — Tiếng Việt>",
  "ai_annotations": [
    {
      "type": "<search_intent|eeat_missing|geo_stats|ai_overview|snippet_ready|entity_gap|geo_fluff|citation_weak|geo_quotes>",
      "text": "<ĐOẠN VĂN NGUYÊN VĂN từ bài viết — substring chính xác, tối đa 200 ký tự>",
      "message": "<hướng dẫn fix CỰC KỲ CỤ THỂ, có ví dụ mẫu — Tiếng Việt>",
      "severity": "<high|warning|info>"
    }
  ]
}

[CALIBRATION — THANG ĐIỂM VIRAL EDGE]
- > 85: TOP 1 READY — Bài viết đủ sức chiến thắng Featured Snippet + AI Overview.
- 70-84: COMPETITIVE — Tốt nhưng cần polish thêm 2-3 tiêu chí để lên Top.
- 50-69: NEEDS WORK — Nội dung đạt mức trung bình, cần cải thiện nhiều.
- < 50: WEAK — Quá nhiều fluff, thiếu data, không đủ sức cạnh tranh AI Search.

[QUY TẮC BẮT BUỘC]
1. Nếu `geo_score` < 95: BẮT BUỘC có nhất 2-5 `ai_annotations` chỉ ra chính xác đoạn nào yếu.
2. Tuyệt đối KHÔNG để trống `ai_annotations` nếu chưa đạt điểm tối đa.
3. KHÔNG TRỪ ĐIỂM cho: thuật ngữ SEO bắt buộc, tên riêng, trích dẫn pháp luật.
4. Mỗi annotation phải có `message` hướng dẫn fix CỤ THỂ, kèm ví dụ viết lại.
5. `text` trong annotation phải là SUBSTRING CHÍNH XÁC từ bài viết (để frontend highlight đúng vị trí).
"""

SURGEON_PROMPT = """[ROLE] VIRAL EDGE SURGICAL AGENT — XoHi Content Intelligence

[NHIỆM VỤ]
Bạn được cung cấp Toàn bộ Bài viết (để lấy ngữ cảnh), một Đoạn văn bị chỉ lỗi (Target Snippet), và Lý do lỗi.
Nhiệm vụ: CHỈ viết lại đúng đoạn Target Snippet đó sao cho khắc phục được lỗi, giữ nguyên văn phong và ngữ cảnh.

[QUY TẮC PHẪU THUẬT THEO LOẠI LỖI]
1. KHÔNG VIẾT LẠI TOÀN BỘ BÀI nếu chỉ sửa 1 đoạn. Nhưng nếu là "Bulk Fix", hãy viết lại các đoạn bị lỗi.
2. Trả về JSON: `{"old_text": "...", "new_text": "..."}` (đơn lẻ) hoặc `{"new_content": "..."}` (Bulk Fix).

[FIX RULES BY ANNOTATION TYPE]
- **search_intent**: Thêm câu trả lời trực tiếp vào đầu đoạn, match đúng intent tìm kiếm.
- **eeat_missing**: Thêm trích dẫn chuyên gia ("Theo chuyên gia X..."), case study thực tế, hoặc số liệu nghiên cứu.
- **geo_stats**: Thêm con số/% cụ thể kèm nguồn (có thể ước lượng hợp lý: "Tăng khoảng 20-30%...").
- **ai_overview**: Cấu trúc lại thành format hỏi-đáp hoặc thêm định nghĩa đầu section ("X là...").
- **snippet_ready**: Rút gọn thành câu trả lời ≤40 từ, hoặc chuyển thành bullet list/bảng so sánh.
- **entity_gap**: Thay thế cụm từ chung chung bằng entity cụ thể (tên, số, thuật ngữ chuyên ngành).
- **geo_fluff**: Cắt gọn câu sáo rỗng, giữ lại chỉ thông tin có giá trị.
- **citation_weak**: Thêm Topic Sentence đầu đoạn, kết luận súc tích cuối đoạn, số liệu kèm ngữ cảnh.
- **geo_quotes**: Thêm cụm "Theo báo cáo/chuyên gia..." kèm tên + chức danh.
- **copyright**: Structural Mutation — thay đổi hoàn toàn cấu trúc câu, không chỉ thay từ đồng nghĩa.

[YÊU CẦU QUAN TRỌNG]
- KHÔNG thay đổi tiêu đề (H1) và Keywords đã chốt ở Step 1.
- Đảm bảo văn phong nhất quán, chuyên nghiệp và súc tích.
"""

class AutoFixRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    target_snippet: str
    annotation_type: str
    error_message: str

class AiInspector:
    """
    On-Demand AI-Readiness (GEO) Analyzer for Step 4 Content Studio.
    Uses Gemini AI to evaluate content against Princeton's GEO heuristics.
    Returns exact-match text snippets for frontend Tiptap highlighting.
    """

    # CNS Phase 82.35: Class-Level Resource Shielding (Global Semaphore)
    _geo_semaphore = asyncio.Semaphore(1)

    def __init__(self):
        # BUG-07 fix: Cache Agents at class scope — R1.6 prohibits per-request Agent creation
        self._geo_agent = Agent(
            system_prompt="Bạn là một hệ thống trả về JSON hợp lệ tuyệt đối theo đúng schema quy định. Bắt buộc dùng Tiếng Việt.",
            output_type=AiReadyReport,
            retries=3
        )
        self._surgeon_agent = Agent(
            system_prompt="Bạn là một hệ thống trả về JSON hợp lệ tuyệt đối. Bắt buộc dùng Tiếng Việt.",
            output_type=AutoFixResponse,
            retries=3
        )
        self._bulk_surgeon_agent = Agent(
            system_prompt="Bạn là hệ thống phẫu thuật nội dung hàng loạt. Trả về JSON theo schema BulkFixResponse. Trả về toàn bộ nội dung bài viết mới.",
            output_type=BulkFixResponse,
            retries=2
        )

    async def analyze(self, campaign: ContentCampaign) -> AiReadyReport:
        """
        Performs full GEO analysis on draft content using Trinity Bridge.
        CNS Phase 82.35: Enforce GLOBAL serial processing for AI READINESS.
        """
        async with self._geo_semaphore:
            draft = campaign.draft_content or ""
        # Phase 76.3: Unified Logic-First Sanitization
        # clean_draft keeps HTML for AI structure analysis, pure_text for exact word counts
        clean_draft = await noise_cleaner.clean(draft, mode="light", strip_html=False)
        pure_text = await noise_cleaner.clean(draft, mode="light", strip_html=True)

        content_sample = clean_draft[:12000]

        try:
            # Use the global trinity_bridge (V61.0 architecture)
            # CNS V76: Use ROLE_BRAIN for elite evaluation
            response = await trinity_bridge.run(
                agent=self._geo_agent,
                prompt=f"{GEO_ANALYSIS_PROMPT}\n\n[NỘI DUNG BÀI VIẾT]\n{content_sample}",
                role="brain"
            )
            return response.data if hasattr(response, 'data') else response.output # This is an AiReadyReport object
        except Exception as e:
            logger.error(f"[AiInspector] AI analysis failed: {e}")
            # R103: Graceful Degradation — rule-based GEO score
            has_stats = any(c.isdigit() for c in pure_text)
            has_quotes = "theo" in pure_text.lower() or "trích dẫn" in pure_text.lower()
            word_count = len(pure_text.split())
            
            base_score = 60
            if has_stats: base_score += 10
            if has_quotes: base_score += 10
            if word_count > 800: base_score += 10
            
            return AiReadyReport(
                geo_score=min(100, base_score),
                summary=f"Phân tích AI tạm thời gián đoạn. Điểm GEO ước tính dựa trên cấu trúc: {base_score}/100.",
                ai_annotations=[
                    AiAnnotation(type="geo_fluff", text="", message="⚠️ AI đang bận, sếp hãy kiểm tra độ súc tích của các đoạn văn nhé!", severity="info")
                ]
            )

    async def auto_fix(self, campaign: ContentCampaign, req: AutoFixRequest) -> AutoFixResponse:
        """
        Contextual Local Rewrite: Rewrites ONLY the targeted snippet to fix the identified analysis error.
        """
        draft = campaign.draft_content or ""
        
        prompt = f"""
{SURGEON_PROMPT}

[NGỮ CẢNH BÀI VIẾT (ĐỂ THAM KHẢO VĂN PHONG)]
{draft[:3000]}...

[YÊU CẦU PHẪU THUẬT]
- Đoạn cần sửa (old_text): "{req.target_snippet}"
- Loại lỗi (type): "{req.annotation_type}"
- Phân tích lỗi từ Hệ thống (message): "{req.error_message}"

Hãy viết lại đoạn văn trên để khắc phục lỗi.
"""
        try:
            agent = self._surgeon_agent
            response = await trinity_bridge.run(
                agent=agent,
                prompt=prompt
            )
            raw_data = response.data if hasattr(response, 'data') else response.output
            
            # Phase 76.3: Physical noise stripping for the Editor
            if isinstance(raw_data, str):
                return AutoFixResponse(old_text=req.target_snippet, new_text=await noise_cleaner.clean(raw_data, mode="aggressive", strip_html=False))
            
            if hasattr(raw_data, "new_text"):
                raw_data.new_text = await noise_cleaner.clean(raw_data.new_text, mode="aggressive", strip_html=False)
            
            return raw_data
        except Exception as e:
            logger.error(f"[AiInspector] Auto-fix failed: {e}")
            return AutoFixResponse(
                old_text=req.target_snippet,
                new_text=req.target_snippet # Return original on failure
            )

    async def bulk_fix(self, campaign: ContentCampaign, req: BulkFixRequest) -> BulkFixResponse:
        """
        Phase 46.1: Bulk correction via Master Surgeon.
        V76.3: Integrates Logic-First HFS Sanitization and Structural Mutation.
        """
        draft = campaign.draft_content or ""
        # Phase 76.3: Clean draft artifacts — KEEP HTML for SEO structure!
        draft = await noise_cleaner.clean(draft, mode="aggressive", strip_html=False)
        
        # Limit to 40 annotations (Phased increase for 2026 context windows)
        valid_annotations = cast(List[Dict[str, object]], [a for a in req.annotations if a.get("text") or a.get("type")])
        if len(valid_annotations) > 40:
            valid_annotations = valid_annotations[:40]

        # Format annotations for AI
        annot_list = ""
        for i, a in enumerate(valid_annotations):
            msg = a.get('message', '') or a.get('reason', '')
            annot_list += f"\n[Lỗi {i+1}]:\n- Đoạn văn: \"{a.get('text', '')}\"\n- Vấn đề: {msg}\n"

        prompt = f"""
[ROLE] EXTREME NEURAL OPTIMIZER — XoHi VIRAL 2026 EDITION

[BÀI VIẾT HIỆN TẠI]
{draft}

[DANH SÁCH LỖI {req.category.upper()} CẦN PHẢI DIỆT TRỪ]
{annot_list}

[NHIỆM VỤ - THUẬT TOÁN EPISODIC REWRITING 2026]
Sếp yêu cầu bài viết này PHẢI đạt điểm chất lượng tuyệt đối (>95%). Bạn không được phép làm việc hời hợt. Hãy thực hiện:

1. **ULTRA-DATA INJECTION**: Bắt buộc "bơm" vào bài viết các thông số kỹ thuật, số liệu tăng trưởng, hoặc kết quả nghiên cứu cụ thể (ví dụ: "Tăng 42.8% hiệu suất so với bản cũ...", "Cắt giảm 15 phút thời gian chờ..."). Không dùng "nhiều", "ít", "đáng kể". Dùng CON SỐ.
2. **AUTHORITY BRANDING**: Viết lại các đoạn văn theo phong cách của một chuyên gia hàng đầu (Thought Leader). Sử dụng các cụm từ thể hiện sự tự tin và chuyên sâu. Thêm các câu trích dẫn "Theo kinh nghiệm của đội ngũ chuyên gia công nghệ..." để tăng EEAT.
3. **MỚI MẺ 100% (INFORMATION GAIN)**: Phá nát các motif cũ. Cung cấp một góc nhìn "độc bản" mà sếp chưa từng thấy ở đối thủ. 
4. **FEATURED SNIPPET DOMINATION**: Mỗi H2 phải đi kèm một đoạn trả lời trực tiếp (Direct Answer) cực kỳ sắc sảo và súc tích.
5. **ASSET FIDELITY**: Tuyệt đối không xóa bất kỳ thẻ [IMAGE_N] nào. Giữ nguyên toàn bộ cấu trúc HTML.

=> MỤC TIÊU: Một kiệt tác SEO không tỳ vết. Sếp phải WOW khi thấy điểm 95+.

Trả về toàn bộ nội dung bài viết mới trong trường `new_content` của JSON.
"""
        try:
            # Phase 82.50: Elite Neural Surgeon — Use ROLE_BRAIN + High Temp for variety
            response = await trinity_bridge.run(
                agent=self._bulk_surgeon_agent,
                prompt=prompt,
                role="brain",
                model_settings={"temperature": 0.8}
            )
            raw_data = response.data if hasattr(response, 'data') else response.output
            if isinstance(raw_data, str):
                # Phase 76.3: Physical noise stripping for the Editor
                return BulkFixResponse(new_content=await noise_cleaner.clean(raw_data, mode="aggressive", strip_html=False))
            
            if hasattr(raw_data, "new_content"):
                raw_data.new_content = await noise_cleaner.clean(raw_data.new_content, mode="aggressive", strip_html=False)
                
            return raw_data
        except Exception as e:
            logger.error(f"[AiInspector] Bulk-fix failed: {e}")
            return BulkFixResponse(new_content=draft) # Fallback to original
