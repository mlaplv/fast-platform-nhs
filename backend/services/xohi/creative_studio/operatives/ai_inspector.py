import re
import logging
from typing import List
from pydantic import BaseModel
from pydantic_ai import Agent
from backend.database.models import ContentCampaign
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

# ══════════════════════════════════════════════════════════════
# SCHEMAS — Generative Engine Optimization (GEO) 2026
# ══════════════════════════════════════════════════════════════

class AiAnnotation(BaseModel):
    type: str      # "geo_stats" | "geo_quotes" | "geo_fluff" | "geo_snippet"
    text: str      # Exact substring from the article to highlight
    message: str   # Vietnamese tip shown in tooltip
    severity: str  # "high" | "warning" | "info"

class AiReadyReport(BaseModel):
    geo_score: int                 # 0-100 score
    summary: str                   # 1-2 line Vietnamese overall verdict
    ai_annotations: List[AiAnnotation] # per-passage inline annotations for editor

# ══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — AI GEO Auditor 2026
# ══════════════════════════════════════════════════════════════

GEO_ANALYSIS_PROMPT = """[ROLE] CHUYÊN GIA GEO (Generative Engine Optimization) 2026

[BỐI CẢNH]
Bạn là chuyên gia phân tích nội dung để đề xuất cho các AI Bots (ChatGPT Search, Perplexity, Google AI Overviews).
Bạn hiểu rõ: LLM KHÔNG quan tâm đến câu văn hoa mỹ. LLM săn tìm:
1. Dữ liệu (Numbers/Stats)
2. Trích dẫn chuyên gia (Citations/Entities)
3. Đi thẳng vào vấn đề (Zero Fluff)
4. Cấu trúc đóng gói (Quotable Snippet - TL;DR dưới mỗi Heading)

[NHIỆM VỤ]
1. Chấm điểm bài viết theo thang 100 dựa trên độ "AI-Friendly" (khả năng được AI bốc làm nguồn).
2. Tìm và "khoanh vùng" (nhổ chính xác từng câu) những đoạn vi phạm 4 Quy Tắc GEO ở dưới, gán vào danh sách `ai_annotations`.

[4 QUY TẮC BẮT LỖI GEO]
1. Lỗi "geo_stats" (Thiếu số liệu, chung chung): 
   - Tìm các câu khẳng định chủ quan như "Tăng trưởng rất mạnh", "Nhiều người dùng".
   - `message` gợi ý: Yêu cầu thay thế bằng con số, % cụ thể để AI có dữ liệu.
   - `severity`: "high" (Đỏ)

2. Lỗi "geo_quotes" (Thiếu trích dẫn E-E-A-T):
   - Tìm những lời khuyên/kiến thức chuyên môn nhưng không ghi rõ cấu trúc "Theo ông X" hoặc "Dựa trên báo cáo Y".
   - `message` gợi ý: Yêu cầu bổ sung nguồn thực thể (Entity) đáng tin cậy.
   - `severity`: "warning" (Cam)

3. Lỗi "geo_fluff" (Văn phong dài dòng / Filler):
   - Tìm những câu dẫn dắt vô nghĩa như "Một trong những điều quan trọng nhất là...", "Như chúng ta đã biết...".
   - `message` gợi ý: Xóa bỏ, đi thẳng vào ý chính. AI ghét sự lê thê.
   - `severity`: "high" (Đỏ)

4. Lỗi "geo_snippet" (Không có câu chốt dưới H2/H3):
   - Xét đoạn văn ngay dưới thẻ Heading (nếu bài viết có HTML tags). Nếu 50 chữ đầu tiên là dẫn dắt vòng vo thay vì trả lời thẳng câu hỏi.
   - `message` gợi ý: Thêm 1 câu TL;DR (<50 từ) tóm gọn ý chính để AI dễ bốc làm Quick Answer.
   - `severity`: "warning" (Cam)

[ĐẦU RA — JSON CHÍNH XÁC]
{
  "geo_score": <int 0-100>,
  "summary": "<1-2 câu nhận xét tổng quát tiếng Việt về mật độ thông tin và độ thân thiện với AI của bài viết>",
  "ai_annotations": [
    {
      "type": "<geo_stats|geo_quotes|geo_fluff|geo_snippet>",
      "text": "<CÂU VĂN NGUYÊN VĂN từ bài viết — phải là substring chính xác để hệ thống bôi màu>",
      "message": "<chỉ dẫn cụ thể bằng tiếng Việt>",
      "severity": "<high|warning|info>"
    }
  ]
}

QUY TẮC VỀ `ai_annotations[].text`:
- PHẢI là chuỗi ký tự NGUYÊN VĂN lấy từ phần nội dung bài viết do user cung cấp (không paraphrase, không tự bịa).
- Tối đa 150 ký tự mỗi annotation (thường là 1 câu).
- Ưu tiên những câu lỗi nhất. Tối đa 10 annotations.
- KHÔNG trả về markdown dư thừa ngoài khối JSON."""


class AutoFixRequest(BaseModel):
    target_snippet: str
    annotation_type: str
    error_message: str

class AutoFixResponse(BaseModel):
    old_text: str
    new_text: str

SURGEON_PROMPT = """[ROLE] AI CHUYÊN GIA DỰNG LẠI NỘI DUNG (Surgical Agent)

[NHIỆM VỤ]
Bạn được cung cấp Toàn bộ Bài viết (để lấy ngữ cảnh), một Đoạn văn bị chỉ lỗi (Target Snippet), và Lý do lỗi.
Nhiệm vụ của bạn là CHỈ viết lại đúng đoạn Target Snippet đó sao cho khắc phục được lỗi, giữ nguyên văn phong và ngữ cảnh của toàn bài.

[QUY TẮC]
1. KHÔNG VIẾT LẠI TOÀN BỘ BÀI. Chỉ viết lại đúng 1 đoạn thay thế cho `target_snippet`.
2. Trả về JSON theo đúng định dạng `{"old_text": "...", "new_text": "..."}`.
3. Nếu lỗi là "Thiếu số liệu (geo_stats)", hãy thêm một con số ước lượng hợp lý hoặc giả lập một thống kê minh họa.
4. Nếu lỗi là "Thiếu nguồn (geo_quotes)", hãy tự thêm cụm "Theo báo cáo/chuyên gia...".
5. Nếu lỗi là "Dông dài (geo_fluff)", hãy cắt gọn nó lại cực kỳ súc tích.
6. Nếu lỗi là "Bản quyền (copyright)", hãy dùng vốn từ đồng nghĩa thay thế hoàn toàn cấu trúc câu mà vẫn giữ nguyên ý nghĩa."""

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

    async def analyze(self, campaign: ContentCampaign) -> AiReadyReport:
        """
        Performs full GEO analysis on draft content using Trinity Bridge.
        """
        draft = campaign.draft_content or ""
        
        # Clean up HTML for token efficiency, but keep it similar enough for substring matching
        plain_text = re.sub(r'<[^>]+>', ' ', draft)
        # Phase 71.20: Strip [IMAGE_N] to match frontend editor content
        plain_text = re.sub(r'\[IMAGE_\d+\]', '', plain_text)
        plain_text = re.sub(r'\s+', ' ', plain_text).strip()

        # Build chunks if content is too large, otherwise grab first 5000 chars
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
            return response.data if hasattr(response, 'data') else response.output
        except Exception as e:
            logger.error(f"[AiInspector] Auto-fix failed: {e}")
            return AutoFixResponse(
                old_text=req.target_snippet,
                new_text=req.target_snippet # Return original on failure
            )
