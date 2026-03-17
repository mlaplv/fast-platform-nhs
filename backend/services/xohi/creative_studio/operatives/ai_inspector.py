import re
import logging
from typing import List, Dict, Union, Optional, Any, cast
from pydantic import BaseModel, ConfigDict
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.noise_cleaner import noise_cleaner
from backend.services.xohi.creative_studio.models.schemas import AiReadyReport, AutoFixResponse, BulkFixResponse, BulkFixRequest

logger = logging.getLogger("api-gateway")

# Phase 76.3: Unified Architecture — Sanitization moved to NoiseCleaner

# ══════════════════════════════════════════════════════════════
# SCHEMAS — Generative Engine Optimization (GEO) 2026
# ══════════════════════════════════════════════════════════════

class AiAnnotation(BaseModel):
    model_config = ConfigDict(strict=True)
    type: str      # "geo_stats" | "geo_quotes" | "geo_fluff" | "geo_snippet"
    text: str      # Exact substring from the article to highlight
    message: str   # Vietnamese tip shown in tooltip
    severity: str  # "high" | "warning" | "info"

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — AI GEO Auditor 2026
# ══════════════════════════════════════════════════════════════

GEO_ANALYSIS_PROMPT = """[ROLE] CHUYÊN GIA GEO (Generative Engine Optimization) 2026
Nhiệm vụ: Đánh giá khả năng bài viết được các AI Search Engine (Perplexity, GPT-4, Gemini) trích dẫn.
Yêu cầu: CHẤM ĐIỂM NGHIÊM KHẮC — Sự thật (Facts) quan trọng hơn văn chương.

[QUY TẮC CHẤM ĐIỂM]
1. geo_stats (Dữ liệu & Con số): 
   - Nếu bài viết toàn từ cảm tính ("rất nhiều", "hiệu quả cao") mà không có con số cụ thể (%, $, triệu...) → TRỪ ĐIỂM NẶNG.
   - AI chỉ tin vào dữ liệu cứng.

2. geo_quotes (Thẩm quyền - Citation):
   - Mọi khẳng định chuyên môn phải có nguồn ("Theo nghiên cứu của X", "Báo cáo Y cho biết").
   - Nếu bài viết nói khơi khơi như ý kiến cá nhân → ĐIỂM THẤP.

3. geo_fluff (Đậm đặc thông tin):
   - Loại bỏ các câu dẫn dắt rỗng tuếch ("Trong thế giới ngày nay...", "Như chúng ta đã biết").
   - AI ghét lãng phí tokens. Nếu mật độ thông tin thấp → TRỪ ĐIỂM.

4. geo_snippet (Cấu trúc Quick Answer):
   - Dưới mỗi heading H2/H3 phải có 1 câu định nghĩa sắc bén (TL;DR).
   - Nếu vòng vo → KHÔNG ĐẠT.

[YÊU CẦU ĐẦU RA — JSON]
{
  "geo_score": <int 0-100 — Chỉ cho >80 nếu bài viết cực kỳ giàu dữ liệu và trích dẫn>,
  "summary": "<Nhận xét trung thực về mật độ thông tin — Tiếng Việt>",
  "ai_annotations": [
    {
      "type": "<geo_stats|geo_quotes|geo_fluff|geo_snippet>",
      "text": "<CÂU VĂN NGUYÊN VĂN từ bài viết>",
      "message": "<chỉ dẫn chính xác cách bổ sung dữ liệu/trích dẫn — tiếng Việt>",
      "severity": "<high|warning|info>"
    }
  ]
}

CALIBRATION:
- > 85: Sẵn sàng để AI bốc làm Quick Answer (Giàu số liệu, nguồn uy tín).
- 70-84: Tốt về thông tin nhưng cần đóng gói lại súc tích hơn.
- 50-69: Nội dung còn mỏng, mang tính chất blog cá nhân hơn là tài liệu tham khảo chuyên sâu.
- < 50: Quá nhiều văn hoa, thiếu dữ liệu thực tế."""

class AutoFixRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    target_snippet: str
    annotation_type: str
    error_message: str

SURGEON_PROMPT = """[ROLE] AI CHUYÊN GIA DỰNG LẠI NỘI DUNG (Surgical Agent)

[NHIỆM VỤ]
Bạn được cung cấp Toàn bộ Bài viết (để lấy ngữ cảnh), một Đoạn văn bị chỉ lỗi (Target Snippet), và Lý do lỗi.
Nhiệm vụ của bạn là CHỈ viết lại đúng đoạn Target Snippet đó sao cho khắc phục được lỗi, giữ nguyên văn phong và ngữ cảnh của toàn bài.

[QUY TẮC]
1. KHÔNG VIẾT LẠI TOÀN BỘ BÀI nếu chỉ sửa 1 đoạn. Nhưng nếu là "Bulk Fix", hãy viết lại các đoạn bị lỗi và đảm bảo chúng khớp với nhau.
- Mô tả lỗi (issue).
- Trả về JSON theo đúng định dạng `{"old_text": "...", "new_text": "..."}` cho case đơn lẻ, hoặc `{"new_content": "..."}` cho Bulk Fix.
- **PHẪU THUẬT CẤU TRÚC (Structural Mutation)**: Nếu lỗi là "Bản quyền (copyright)": Bạn phải thay đổi hoàn toàn cách tiếp cận của đoạn văn. Ví dụ: Nếu bản cũ là kể chuyện (narrative), hãy đổi sang liệt kê phân tích (analytical list); nếu bản cũ ở ngôi thứ nhất, hãy đổi sang ngôi thứ ba. Tuyệt đối không được giữ nguyên bộ khung rồi thay từ đồng nghĩa.
- Nếu lỗi là "Thiếu số liệu (geo_stats)", hãy thêm một con số ước lượng hợp lý hoặc giả lập một thống kê minh họa.
- Nếu lỗi là "Thiếu nguồn (geo_quotes)", hãy tự thêm cụm "Theo báo cáo/chuyên gia...".
- Nếu lỗi là "Dông dài (geo_fluff)", hãy cắt gọn nó lại cực kỳ súc tích.
"""

class AiInspector:
    """
    On-Demand AI-Readiness (GEO) Analyzer for Step 4 Content Studio.
    Uses Gemini AI to evaluate content against Princeton's GEO heuristics.
    Returns exact-match text snippets for frontend Tiptap highlighting.
    """

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
        """
        draft = campaign.draft_content or ""
        
        # Phase 76.3: Unified Logic-First Sanitization
        plain_text = await noise_cleaner.clean(draft, mode="light", strip_html=True)

        content_sample = plain_text[:5000]

        try:
            # Use the global trinity_bridge (V61.0 architecture)
            response = await trinity_bridge.run(
                agent=self._geo_agent,
                prompt=f"{GEO_ANALYSIS_PROMPT}\n\n[NỘI DUNG BÀI VIẾT]\n{content_sample}"
            )
            return response.data if hasattr(response, 'data') else response.output # This is an AiReadyReport object
        except Exception as e:
            logger.error(f"[AiInspector] AI analysis failed: {e}")
            # R103: Graceful Degradation — rule-based GEO score
            has_stats = any(c.isdigit() for c in plain_text)
            has_quotes = "theo" in plain_text.lower() or "trích dẫn" in plain_text.lower()
            word_count = len(plain_text.split())
            
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
        # Phase 76.3: Clean draft artifacts before surgeon audit
        draft = await noise_cleaner.clean(draft, mode="aggressive", strip_html=True)
        
        # Limit to 15 annotations to avoid context overflow
        valid_annotations = cast(List[Dict[str, Any]], [a for a in req.annotations if a.get("text") or a.get("type")])
        if len(valid_annotations) > 15:
            valid_annotations = valid_annotations[:15]

        # Format annotations for AI
        annot_list = ""
        for i, a in enumerate(valid_annotations):
            msg = a.get('message', '') or a.get('reason', '')
            annot_list += f"\n[Lỗi {i+1}]:\n- Đoạn văn: \"{a.get('text', '')}\"\n- Vấn đề: {msg}\n"

        prompt = f"""
[ROLE] MASTER SURGEON AGENT — XoHi 2026

[BÀI VIẾT HIỆN TẠI]
{draft}

[DANH SÁCH LỖI {req.category.upper()}]
{annot_list}

NHIỆM VỤ:
Viết lại TOÀN BỘ bài viết sao cho:
1. Sửa triệt để tất cả các lỗi được liệt kê ở trên.
2. ĐỐI VỚI LỖI COPYRIGHT/DEDUP: Đây là yêu cầu tối quan trọng. Bạn phải viết lại các đoạn này bằng văn phong khác biệt hoàn toàn (đổi cấu trúc, đổi từ vựng, đổi cách đặt vấn đề) sao cho khi kiểm tra lại, tỷ lệ trùng khớp phải bằng 0.
3. KHÔNG thay đổi cấu trúc Heading (H1, H2, H3).
4. Đảm bảo văn phong nhất quán giữa đoạn cũ và đoạn vừa sửa.
5. KHÔNG "bịa" dữ liệu sai sự thật, chỉ tối ưu hóa dựa trên thông tin hiện có hoặc thêm các cụm từ trung lập (ví dụ: "Theo các chuyên gia", "Dữ liệu cho thấy").

Trả về toàn bộ nội dung bài viết mới trong trường `new_content` của JSON.
"""
        try:
            response = await trinity_bridge.run(
                agent=self._bulk_surgeon_agent,
                prompt=prompt
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
