import logging
from typing import Optional, Dict
from pydantic_ai import Agent
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, XoHiProgressMixin
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

_NEURAL_REWRITE_PROMPT = """[ROLE] {role} — XoHi Elite V2.2
Nhiệm vụ: Viết lại toàn bộ nội dung dựa trên các luận điểm phản biện (Copyright Verdict) để đạt 100% Unique và Viral Edge.

[QUY TẮC TÁC CHIẾN — ELITE PROTOCOL]
1. 🔪 TRIỆT ĐỂ: Không chỉ sửa lỗi. Hãy đập đi xây lại cấu trúc nếu cần để mang bản sắc riêng, không còn dấu vết của đối thủ.
2. 💉 INFORMATION GAIN: Sử dụng [DỮ LIỆU THỰC TẾ (FACT SHEET)] làm nguồn tư liệu chính để viết bài. Cấm bịa đặt thông số.
3. 🚫 TỰ CHỦ NỘI DUNG: Không được lặp lại nguyên văn các câu văn cũ. Phải thay đổi cấu trúc câu, từ vựng để đạt điểm Uniqueness cao nhất.
4. ⚡ VIRAL EDGE: Sử dụng ngôn ngữ sắc bén, tiêu đề giật gân nhưng chuyên nghiệp.
5. 🛡️ HTML PRESERVATION: Giữ lại các thẻ HTML quan trọng (<h1>, <h2>, <ul>, <img>, <table>).
6. 🚫 KHÔNG GIẢI THÍCH: Trả về kết quả là NỘI DUNG HTML thuần. CẤM tuyệt đối việc sử dụng các thẻ cấp trang như <!DOCTYPE>, <html>, <head>, <body>. Chỉ trả về cấu trúc nội dung (<h1>, <p>, <ul>, <img>, <table>, ...).
7. 🚫 CẤM BẢO VỆ CODE: Không bao giờ được đặt kết quả trong khối mã markdown (```html). Trả về text HTML trực tiếp.
8. 🚫 KHÔNG LẶP LẠI NHÃN: Tuyệt đối không sử dụng các tiêu đề nhãn từ yêu cầu (ví dụ: "[DỮ LIỆU THỰC TẾ]", "[FACT SHEET]", "[THÔNG TIN PHẢN BIỆN]") vào trong bài viết. Hãy tự đặt các tiêu đề phù hợp với ngữ cảnh bán hàng (ví dụ: "Thông số kỹ thuật", "Giải đáp thắc mắc").
9. 🚫 CẤM TRÙNG LẶP UI: Các thông tin như Thương hiệu, SKU, Xuất xứ, FAQ đã có trong Fact Sheet sẽ bị CẤM viết lại vào nội dung bài viết để tránh dư thừa UI.
10. 🧪 VIRAL SPEC BENTO: Tuyệt đối KHÔNG dùng thẻ <table> để trình bày thông số. Năm 2026, hãy sử dụng cấu trúc Spec Bento Grid chuyên nghiệp sau:
<div class="spec-bento-grid">
  <div class="spec-card">
    <div class="spec-label">Thông số</div>
    <div class="spec-value">Thương hiệu: Beppin Body</div>
  </div>
  ...
</div>

{context_instructions}

[NGUỒN DỮ LIỆU THỰC TẾ]:
{fact_sheet}

[LUẬN ĐIỂM CẦN KHẮC PHỤC]:
{feedback}

{user_note_section}
"""

_PRODUCT_INSTRUCTIONS = """[CHỈ THỊ RIÊNG CHO SẢN PHẨM — GOLD STANDARD V2.2]:
- ROLE: Chuyên gia chốt đơn quốc tế (Global Direct-Response Copywriter).
- GIỌNG ĐIỆU: Sắc bén, chuyên nghiệp, tập trung vào KẾT QUẢ và NIỀM TIN khoa học.
- CẤU TRÚC BẮT BUỘC (Strict Layout):
    1. **Headline (Tiêu đề thôi miên)**: [Tên sản phẩm] + [Lợi ích cốt lõi] + [Con số thực chứng].
    2. **The Hero Identity**: 1-2 câu khẳng định vị thế độc bản (Hero Position).
    3. **The Golden Formula (Thành phần vàng)**: Phân tích 2-3 thành phần chính theo hướng: Thành phần -> Công nghệ -> Kết quả.
    4. **High-Impact Benefits (Công dụng)**: Dạng Bullet Points [Feature -> Benefit]. Giải quyết nỗi đau cụ thể.
    5. **The Ritual (Hướng dẫn sử dụng)**: BẮT BUỘC. Hướng dẫn chi tiết các bước (Làm sạch -> Thẩm thấu -> Khóa ẩm).
    6. **Safety Protocol (Lưu ý & Kiêng cử)**: BẮT BUỘC (EEAT). Cảnh báo về vết thương hở, kỵ hoạt chất, bảo quản.
    7. **The Perfect Routine (Gợi ý kết hợp)**: BẮT BUỘC. Gợi ý Combo tối ưu hiệu quả.

- QUY TẮC VĂN PHONG:
*   Phong cách: High-End Landing Page (Apple/Paula's Choice).
*   Trình bày thông tin rõ ràng, dễ tra cứu, không lan man kiểu blog.
*   🛡️ PREMIUM SPECS: Nếu Sếp yêu cầu hoặc cần thiết, hãy sử dụng cấu trúc [PREMIUM FACT SHEET UI] (Rule #10) để trình bày bảng thông số.
*   🚫 CẤM VIẾT LẠI: Tuyệt đối không trình bày lại các thông số (Thương hiệu, SKU, FAQ) dưới dạng văn bản xuôi (prose) nếu chúng đã có trong bảng thông số hoặc Fact Sheet UI.
"""

_ARTICLE_INSTRUCTIONS = """[CHỈ THỊ RIÊNG CHO BÀI VIẾT — NEURAL JOURNALIST]:
- Tập trung vào Storytelling và giá trị thông tin (Information Gain).
*   Sử dụng dữ liệu trinh sát (Scout Report) để tăng uy tín E-E-A-T.
*   🚫 CẤM SAO CHÉP THÔ: Tuyệt đối không liệt kê lại các thông số (Thương hiệu, SKU, FAQ) thành một danh sách riêng biệt. Hãy lồng ghép chúng vào câu chuyện (Storytelling).
*   Phong cách: Lôi cuốn, sắc bén, chuẩn chuyên gia."""

class NeuralRewriter(BaseAgentOperative, XoHiProgressMixin):
    """
    CNS V88.5: Neural Creative Rewriter.
    Elite V2.2: Context-Aware (Product/Article).
    """
    agent_id_class = "neural_rewriter"

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="neural_rewriter")
        self._agent = Agent(output_type=str, retries=2)

    def _sanitize_html(self, html: str) -> str:
        import re
        # CNS V90.1: Military-grade cleanup.
        # Step 1: Strip everything before the first '<' and after the last '>'
        # This kills ```html and any AI chatter immediately.
        first_tag = html.find('<')
        last_tag = html.rfind('>')
        
        if first_tag != -1 and last_tag != -1:
            html = html[first_tag:last_tag+1]
        
        # Step 2: Nuclear option for any remaining backticks or markdown bits
        html = html.replace('```html', '').replace('```', '')
        
        # Step 3: Strip <!DOCTYPE>, <html>, <head> tags
        html = re.sub(r'<!DOCTYPE.*?>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'<html.*?>', '', html, flags=re.IGNORECASE | re.DOTALL)
        html = re.sub(r'</html>', '', html, flags=re.IGNORECASE)
        html = re.sub(r'<head.*?>.*?</head>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Step 4: Extract content inside <body> if AI was too helpful
        body_match = re.search(r'<body.*?>(.*?)</body>', html, flags=re.IGNORECASE | re.DOTALL)
        if body_match:
            html = body_match.group(1)
        else:
            html = re.sub(r'<body.*?>', '', html, flags=re.IGNORECASE)
            html = re.sub(r'</body>', '', html, flags=re.IGNORECASE)
            
        return html.strip()

    def _generate_fact_sheet(self, metadata: Dict[str, object]) -> str:
        if not metadata: return "Không có dữ liệu bổ sung."
        lines = []
        for k, v in metadata.items():
            if isinstance(v, list):
                v_str = ", ".join([str(i) for i in v])
                lines.append(f"- {k.upper()}: {v_str}")
            elif isinstance(v, dict):
                lines.append(f"- {k.upper()}: {v}")
            else:
                lines.append(f"- {k.upper()}: {v}")
        return "\n".join(lines)

    async def chat(self, request: object, **kwargs: object) -> str:
        """Standard Heritage Entry."""
        content = str(kwargs.get("content", ""))
        topic = str(kwargs.get("topic", ""))
        feedback = str(kwargs.get("feedback", ""))
        campaign_id = str(kwargs.get("campaign_id", "adhoc"))
        content_type = str(kwargs.get("content_type", "article")).lower()
        metadata = kwargs.get("metadata", {}) or {}
        user_note = str(kwargs.get("user_note", "") or "").strip()
        
        role = "CHUYÊN GIA TỐI ƯU SẢN PHẨM" if content_type == "product" else "NHÀ BÁO NEURAL"
        context_instructions = _PRODUCT_INSTRUCTIONS if content_type == "product" else _ARTICLE_INSTRUCTIONS
        fact_sheet = self._generate_fact_sheet(metadata)
        
        user_note_section = ""
        if user_note:
            user_note_section = f"[GHI CHÚ CHIẾN LƯỢC - ƯU TIÊN CAO NHẤT]:\n{user_note}\n"

        logs: list[str] = [
            f"🚀 Neural Creative Rewrite khởi động cho {content_type}: '{topic}'...",
        ]
        await self._emit_progress(campaign_id, logs[-1])

        if not content:
            return "Nội dung trống, không thể viết lại."

        system_prompt = _NEURAL_REWRITE_PROMPT.format(
            role=role,
            context_instructions=context_instructions,
            fact_sheet=fact_sheet,
            feedback=feedback,
            user_note_section=user_note_section
        )
        prompt = f"[TIÊU ĐIỂM]: {topic}\n\n[NỘI DUNG GỐC]:\n{content[:15000]}"

        try:
            logs.append(f"🧠 Đang nạp Fact Sheet & nạp vai {role}...")
            if user_note:
                logs.append(f"📝 Đã nhận chỉ đạo: '{user_note[:30]}...'")
            await self._emit_progress(campaign_id, logs[-1])
            
            logs.append("🖋️ Xohi đang múa bút tái cấu trúc nội dung...")
            await self._emit_progress(campaign_id, logs[-1])
            
            response = await trinity_bridge.run(
                self._agent, 
                prompt, 
                system_prompt=system_prompt,
                role="pro", 
                timeout=120.0
            )
            
            final_text = getattr(response, "data", str(response))
            final_text = self._sanitize_html(final_text)
            
            logs.append("✅ Phẫu thuật sáng tạo hoàn tất! Nội dung mới đã sẵn sàng.")
            await self._emit_progress(campaign_id, logs[-1], status="DONE")
            
            return final_text
        except Exception as exc:
            logger.error(f"[NeuralRewriter] Lỗi viết lại: {exc}", exc_info=True)
            err_msg = f"❌ Lỗi Neural Creative: {str(exc)[:100]}"
            await self._emit_progress(campaign_id, err_msg, status="FAILED")
            return content

# Heritage Backdoor
async def run_neural_rewrite(content: str, topic: str = "", feedback: str = "", campaign_id: str = "adhoc", content_type: str = "article", metadata: Dict[str, object] = None, user_note: Optional[str] = None) -> str:
    rewriter = NeuralRewriter()
    return await rewriter.chat(None, content=content, topic=topic, feedback=feedback, campaign_id=campaign_id, content_type=content_type, metadata=metadata, user_note=user_note)
