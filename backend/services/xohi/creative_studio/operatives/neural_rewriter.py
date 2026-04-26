import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from backend.services.ai_engine.core.agent_base import BaseAgentOperative, XoHiProgressMixin
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge

logger = logging.getLogger("api-gateway")

class ComponentData(BaseModel):
    title: str = Field(..., description="Tiêu đề thành phần hoặc công dụng")
    description: str = Field(..., description="Mô tả chi tiết")

class SpecBento(BaseModel):
    label: str = Field(..., description="Tên thông số (VD: Thương hiệu)")
    value: str = Field(..., description="Giá trị (VD: Beppin Body)")

class RewriteResult(BaseModel):
    """Cấu trúc dữ liệu chuẩn JSON cho Dashboard Interactive UI"""
    hero_headline: str = Field(..., description="Tiêu đề thôi miên (ngắn gọn, giật gân, có số liệu)")
    unique_identity: str = Field(..., description="1-2 câu khẳng định vị thế độc bản")
    spec_bento: List[SpecBento] = Field(..., description="Bảng thông số kỹ thuật (Thương hiệu, SKU, Xuất xứ...)")
    golden_ingredients: List[ComponentData] = Field(..., description="Thành phần vàng & Công nghệ")
    benefits: List[ComponentData] = Field(..., description="Công dụng (Feature -> Benefit)")
    routine: List[str] = Field(..., description="Các bước hướng dẫn sử dụng")
    safety_warnings: List[str] = Field(..., description="Lưu ý an toàn, kiêng cữ")
    combinations: List[str] = Field(..., description="Gợi ý kết hợp (Combo)")
    seo_metadata: str = Field(..., description="Tóm tắt SEO (150 ký tự)")
    generated_at: Optional[str] = Field(None, description="Mốc thời gian lập báo cáo")

_NEURAL_REWRITE_PROMPT = """[ROLE] {role} — XoHi Elite V2.2
Nhiệm vụ: Viết lại toàn bộ nội dung dựa trên các luận điểm phản biện (Copyright Verdict) để đạt 100% Unique và Viral Edge.

[QUY TẮC TÁC CHIẾN — ELITE PROTOCOL]
1. 🔪 TRIỆT ĐỂ: Không chỉ sửa lỗi. Hãy đập đi xây lại cấu trúc nếu cần để mang bản sắc riêng, không còn dấu vết của đối thủ.
2. 💉 INFORMATION GAIN: Sử dụng [DỮ LIỆU THỰC TẾ (FACT SHEET)] làm nguồn tư liệu chính để viết bài. Cấm bịa đặt thông số.
3. 🚫 TỰ CHỦ NỘI DUNG: Không được lặp lại nguyên văn các câu văn cũ. Phải thay đổi cấu trúc câu, từ vựng để đạt điểm Uniqueness cao nhất.
4. ⚡ VIRAL EDGE: Sử dụng ngôn ngữ sắc bén, tiêu đề giật gân nhưng chuyên nghiệp.
5. 🛡️ DATA EXTRACTION ONLY: Bạn CHỈ ĐƯỢC PHÉP TRẢ VỀ DỮ LIỆU THEO ĐÚNG ĐỊNH DẠNG JSON SCHEMA ĐƯỢC CUNG CẤP. Không trả về HTML, không giải thích.
6. 🚫 KHÔNG LẶP LẠI NHÃN: Tuyệt đối không sử dụng các tiêu đề nhãn từ yêu cầu (ví dụ: "[DỮ LIỆU THỰC TẾ]") vào trong nội dung.
7. 🕒 TIMESTAMPS: Luôn điền mốc thời gian hiện tại vào trường `generated_at` nếu có thể.

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
- ĐẢM BẢO CHẤT LƯỢNG: Phân bổ dữ liệu chuẩn xác vào các field của JSON, đặc biệt là `spec_bento` (thông số) và `golden_ingredients` (thành phần).
"""

_ARTICLE_INSTRUCTIONS = """[CHỈ THỊ RIÊNG CHO BÀI VIẾT — NEURAL JOURNALIST]:
- Tập trung vào Storytelling và giá trị thông tin (Information Gain).
- Sử dụng dữ liệu trinh sát để điền vào `benefits` và `golden_ingredients` sao cho lôi cuốn, sắc bén, chuẩn chuyên gia.
"""

class NeuralRewriter(BaseAgentOperative, XoHiProgressMixin):
    """
    CNS V88.5: Neural Creative Rewriter.
    Elite V2.2: Context-Aware (Product/Article) with Data-driven API (JSON Outputs).
    """
    agent_id_class = "neural_rewriter"

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="neural_rewriter")
        self._agent = Agent(output_type=RewriteResult, retries=2)

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

        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        logs: list[str] = [
            f"🚀 [{now_str}] Neural Creative Rewrite khởi động cho {content_type}: '{topic}'...",
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
            logs.append(f"🧠 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Đang nạp Fact Sheet & nạp vai {role}...")
            if user_note:
                logs.append(f"📝 Đã nhận chỉ đạo: '{user_note[:30]}...'")
            await self._emit_progress(campaign_id, logs[-1])
            
            import time
            start_time = time.time()
            response = await trinity_bridge.run(
                self._agent, 
                prompt, 
                system_prompt=system_prompt,
                role="pro", 
                timeout=120.0
            )
            duration = time.time() - start_time
            
            # response.data is an instance of RewriteResult
            res_data = response.data
            res_data.generated_at = datetime.now(timezone.utc).strftime('%H:%M:%S %d/%m/%Y')
            final_json = res_data.model_dump_json()
            
            logs.append(f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Phẫu thuật sáng tạo hoàn tất trong {duration:.1f}s! JSON Pipeline đã sẵn sàng.")
            await self._emit_progress(campaign_id, logs[-1], status="DONE")
            
            return final_json
        except Exception as exc:
            logger.error(f"[NeuralRewriter] Lỗi viết lại: {exc}", exc_info=True)
            err_msg = f"❌ Lỗi Neural Creative: {str(exc)[:100]}"
            await self._emit_progress(campaign_id, err_msg, status="FAILED")
            return content

# Heritage Backdoor
async def run_neural_rewrite(content: str, topic: str = "", feedback: str = "", campaign_id: str = "adhoc", content_type: str = "article", metadata: Dict[str, object] = None, user_note: Optional[str] = None) -> str:
    rewriter = NeuralRewriter()
    return await rewriter.chat(None, content=content, topic=topic, feedback=feedback, campaign_id=campaign_id, content_type=content_type, metadata=metadata, user_note=user_note)
