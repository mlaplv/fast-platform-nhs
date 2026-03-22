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
    GoldMetadata, AiAnnotation, AtomicFixResponse, SurgicalSnippetFix
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
            system_prompt="Bạn là hệ thống phẫu thuật nội dung GEO hàng loạt. Trả về JSON theo schema BulkFixResponse. Trả về toàn bộ nội dung bài viết mới.",
            output_type=BulkFixResponse,
            retries=2
        )
        self._atomic_surgeon_agent = Agent(
            system_prompt="Bạn là hệ thống phẫu thuật nội dung GEO chuyên sâu cấp độ nguyên tử. Trả về AtomicFixResponse.",
            output_type=AtomicFixResponse,
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
        Phase 82.25: Atomic GEO Reconstruction.
        Ensures 100% integrity of non-erroneous content by only processing targeted snippets.
        """
        logs = []
        logs.append("🔍 Khởi động hệ thống tối ưu hóa SEO & AI...")

        # CNS V82.55: Clean draft once to ensure internal consistency for stitching
        draft_content = await noise_cleaner.clean(campaign.draft_content or "", mode="light", strip_html=False)
        valid_annotations = cast(List[Dict[str, object]], [a for a in req.annotations if a.get("text") or a.get("type")])
        
        # ── Phase 82.25: Atomic GEO Reconstruction ──────────────────────────
        # We only send the snippets to the AI to ensure 100% integrity of the rest
        
        snippet_list = ""
        valid_items = []
        for i, a in enumerate(valid_annotations[:40]):
            txt_raw = (a.get('text', '') or "").strip()
            if not txt_raw or len(txt_raw) < 5: continue
            
            # CNS V82.56: SANITIZE old_text from annotation BEFORE matching
            # This ensures that if the draft was cleaned, we match the cleaned version.
            txt = await noise_cleaner.clean(txt_raw, mode="light", strip_html=False)
            
            msg = a.get('message', '') or a.get('reason', '')
            snippet_list += f"\n[ID {i+1}]:\n- Đoạn văn: \"{txt}\"\n- Lỗi: {msg}\n"
            valid_items.append({"id": i+1, "old_text": txt})

        if not valid_items:
            return BulkFixResponse(new_content=draft_content)

        bulk_prompt = f"""
[ROLE] ATOMIC GEO SURGEON — XoHi VIRAL 2026
Nhiệm vụ: Chỉ sửa đúng các đoạn văn được cung cấp trong danh sách dưới đây để tăng tính GEO (Information Gain).
Tuyệt đối không được sửa bất kỳ chữ nào khác ngoài các đoạn này. Trả về AtomicFixResponse.

[DANH SÁCH CÁC ĐOẠN CẦN PHẪU THUẬT]
{snippet_list}

[6 NGUYÊN TẮC VÀNG — BẢO TỒN NỘI DUNG TỐT]
1. 💎 STRATEGIC DATA INJECTION: Không viết chung chung. Phải thêm các con số, tỷ lệ %, mốc thời gian hoặc insight chuyên gia vào các đoạn sửa.
2. 🧩 HTML PRESERVATION: Giữ nguyên 100% thẻ [IMAGE_N] và các thẻ HTML (h2, h3, p) có trong đoạn.
3. 🛡️ ATOMIC FIX: Chỉ trả về đoạn văn đã sửa trong AtomicFixResponse theo đúng ID.
4. 🚀 AUTHORITY & TRUST: Dùng tông giọng chuyên nghiệp, sắc bén. Cấm dùng từ sáo rỗng (fluff).
5. 🎯 CONSISTENCY: Duy trì văn phong nhất quán với toàn bài.
6. 🛡️ DATA INTEGRITY: Không bịa đặt số liệu sai lệch bối cảnh bài viết.

Trả về danh sách các đoạn đã sửa trong trường `replacements` của JSON.
"""
        if valid_items:
            logs.append(f"🧠 Đang xử lý {len(valid_items)} đoạn cần tối ưu qua AI...")

        try:
            res = await trinity_bridge.run(
                self._atomic_surgeon_agent,
                bulk_prompt,
                role="fast", # Atomic precision doesn't need high reasoning, just surgical stability
                model_settings={"temperature": 0.3},
                timeout=120.0 # High timeout for complex phẫu thuật
            )
            raw_data = res.data if hasattr(res, 'data') else res.output
            
            # Atomic Stitching Layer (The "Memo"): Use the original draft and only swap fixed parts
            final_content = draft_content
            replacements_made = 0
            
            if hasattr(raw_data, "replacements"):
                # Sort replacements by length descending to avoid sub-string replacement issues
                sorted_fixes = sorted(raw_data.replacements, key=lambda x: len(next((v["old_text"] for v in valid_items if v["id"] == x.id), "")), reverse=True)
                
                for fix in sorted_fixes:
                    orig_item = next((v for v in valid_items if v["id"] == fix.id), None)
                    if orig_item and fix.new_text:
                        old_txt = orig_item["old_text"]
                        new_txt = await noise_cleaner.clean(fix.new_text, mode="light", strip_html=False)
                        
                        # Only replace if target exists to maintain integrity
                        # Phase 82.65: Robust Relaxed Match
                        if old_txt in final_content:
                            final_content = final_content.replace(old_txt, new_txt)
                            replacements_made += 1
                            msg = f"✅ Đã tối ưu xong: \"{old_txt[:30]}...\""
                            logger.info(f"[AiInspector] {msg}")
                            logs.append(msg)
                        else:
                            # Try 'Relaxed Match' (ignore whitespace/special chars)
                            from backend.utils.noise_cleaner import RE_WHITESPACE
                            norm_old = RE_WHITESPACE.sub('', old_txt)
                            if len(norm_old) > 20: 
                                # This is a bit expensive but extremely reliable for surgical precision
                                match_found = False
                                # We search for a segment that normalizes to the same thing
                                for start_idx in range(len(final_content) - len(old_txt) + 20):
                                    window = final_content[start_idx : start_idx + len(old_txt) + 20]
                                    if RE_WHITESPACE.sub('', window).startswith(norm_old):
                                        # Found it! Determine actual end by finding where norm_old ends
                                        actual_match = final_content[start_idx : start_idx + len(old_txt)]
                                        final_content = final_content.replace(actual_match, new_txt)
                                        replacements_made += 1
                                        match_found = True
                                        logger.info(f"[AiInspector] Relaxed match successful for ID {fix.id}")
                                        break
                                
                                if not match_found:
                                    logger.warning(f"[AiInspector] Surgical match failed for ID {fix.id}. Snippet not found even with relaxed match.")
                            else:
                                logger.warning(f"[AiInspector] Surgical match failed for ID {fix.id}. Snippet too short for relaxed match.")

            logs.append(f"🏅 Hoàn tất! Đã tối ưu {replacements_made} phân đoạn.")
            return BulkFixResponse(new_content=final_content, logs=logs)
        except Exception as e:
            logger.error(f"[AiInspector] Atomic bulk-fix failed: {e}")
            logs.append(f"❌ Có lỗi xảy ra: {str(e)}")
            return BulkFixResponse(new_content=draft_content, logs=logs)
