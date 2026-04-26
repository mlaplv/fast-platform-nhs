import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from backend.services.ai_engine.core.agent_base import BaseAgentOperative
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.shields.service import shield_service

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

class NeuralRewriter(BaseAgentOperative):
    """
    CNS V88.5: Neural Creative Rewriter.
    Elite V2.2: Context-Aware (Product/Article) - Restored to Tiptap-Ready HTML.
    """
    agent_id_class = "neural_rewriter"

    def __init__(self, **kwargs: object):
        super().__init__(agent_id="neural_rewriter")
        self._agent = Agent(output_type=str, retries=2)

    # ELITE V2.2: Fields that are already displayed as static metadata on the product page
    _EXCLUDED_META_KEYS: tuple[str, ...] = ("brand", "origin", "sku", "weight", "category", "unit")

    def _generate_fact_sheet(self, metadata: Dict[str, object]) -> str:
        """Generate fact sheet, excluding static display fields (Rule 10: Redundancy Kill)."""
        if not metadata:
            return "Không có dữ liệu bổ sung."
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

    def _generate_excluded_fields_section(self, metadata: Dict[str, object]) -> str:
        """Extract static metadata fields so AI knows NOT to repeat them (Rule 10)."""
        excluded: list[str] = []
        for key in self._EXCLUDED_META_KEYS:
            val = metadata.get(key)
            if val:
                excluded.append(f"- {key.upper()}: {val}")
        if not excluded:
            return ""
        lines = "\n".join(excluded)
        return (
            "[DANH SÁCH THÔNG TIN TĨNH — TUYỆT ĐỐI KHÔNG LẶP LẠI]:\n"
            "(Những trường dưới đây đã hiển thị trên trang sản phẩm/bài viết, "
            "AI không được phép đề cập lại dưới bất kỳ hình thức nào)\n"
            f"{lines}\n"
        )

    async def chat(self, request: object, **kwargs: object) -> str:
        """Standard Heritage Entry."""
        content = str(kwargs.get("content", ""))
        topic = str(kwargs.get("topic", ""))
        feedback = str(kwargs.get("feedback", ""))
        campaign_id = str(kwargs.get("campaign_id", "adhoc"))
        content_type = str(kwargs.get("content_type", "article")).lower()
        metadata = kwargs.get("metadata", {}) or {}
        user_note = str(kwargs.get("user_note", "") or "").strip()
        
        user_note = str(kwargs.get("user_note", "") or "").strip()
        
        shield = shield_service.get_shield_component(seed=campaign_id)
        composer.register_component(shield)
        
        # [CNS-V89] Resolve Context via Centralized Intelligence
        context = await self._resolve_xohi_context(metadata, content, "rewriter")
        role = context["role_assignment"]
        
        template_name = "rewriter_product" if context["is_product"] else "rewriter_article"
        # ELITE V2.2: Use extra_components to maintain thread-safety
        system_prompt_base = composer.compose(template_name, extra_components=[shield.id])
        
        logger.info(f"🛡️ [NeuralRewriter] [ROLE] Đã xác nhận phân vai tác chiến: {role}")
        logger.info(f"🛡️ [NeuralRewriter] [SHIELD] Đã kích hoạt SGE Shield V2.1 (Anti-AI Footprint)")
        logger.info(f"🛡️ [NeuralRewriter] [SAFETY] Chế độ Ad-hoc Safety: {'ACTIVE' if campaign_id == 'adhoc' else 'CAMPAIGN_MODE'}")
        fact_sheet = self._generate_fact_sheet(metadata)
        excluded_fields_section = self._generate_excluded_fields_section(metadata)

        user_note_section = ""
        if user_note:
            user_note_section = f"[GHI CHÚ CHIẾN LƯỢC - ƯU TIÊN CAO NHẤT]:\n{user_note}\n"

        # Final assembly of dynamic sections into the NPO base (Rule 10: excluded fields injected)
        system_prompt = system_prompt_base.format(
            role_assignment=role,
            content_foundation=content[:25000],  # Foundation limit: Increased to 25k for rich HTML preservation
            fact_sheet=fact_sheet,
            feedback=feedback,
            user_note_section=user_note_section
        )
        if excluded_fields_section:
            system_prompt = excluded_fields_section + "\n" + system_prompt

        self.current_step = 0
        now_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        logs: list[str] = [
            f"🚀 [{now_str}] Neural Creative Rewrite khởi động cho {content_type}: '{topic}'...",
        ]
        await self._emit_progress(campaign_id, logs[-1])
        logger.warning(f"🚀 [NeuralRewriter] Initializing [SCAN] Phase for {content_type}...")

        if not content:
            return "Nội dung trống, không thể viết lại."

        prompt = f"[TIÊU ĐIỂM]: {topic}\n\n[NỘI DUNG GỐC]:\n{content[:15000]}\n\n[PHẢN BIỆN & YÊU CẦU]:\n{feedback}"

        try:
            self.current_step = 1
            logs.append(f"🧠 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [FACTS] Đang nạp Fact Sheet & nạp vai {role}...")
            if user_note:
                logs.append(f"📝 Đã nhận chỉ đạo: '{user_note[:30]}...'")
            await self._emit_progress(campaign_id, logs[-1])
            logger.warning(f"🧠 [NeuralRewriter] Phase 1: [FACTS] Context Ingestion complete.")
            
            self.current_step = 2
            logger.warning(f"🧠 [NeuralRewriter] Phase 2: [CREATIVE] Brain processing pending...")
            import time
            start_time = time.time()
            
            # ELITE V2.2: Restoration of Tiptap-Ready HTML (Sếp's Order)
            response = await trinity_bridge.run(
                self._agent, 
                prompt, 
                system_prompt=system_prompt,
                role="pro", 
                timeout=150.0
            )
            duration = time.time() - start_time
            
            # ELITE V2.2: Universal Sanitization (Tiptap Ready)
            content_raw = str(getattr(response, "data", response))
            sanitized_content = self.clean_ai_html(content_raw)
            sanitized_content = shield_service.sanitize(sanitized_content)
            
            self.current_step = 3
            logs.append(f"✅ [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] [QUANTUM] Phẫu thuật sáng tạo hoàn tất trong {duration:.1f}s! Đã cập nhật vào Tiptap. ĐÃ XỬ LÝ XONG")
            await self._emit_progress(campaign_id, logs[-1], status="DONE")
            logger.warning(f"✅ [NeuralRewriter] [QUANTUM] Creative Rewrite complete (HTML).")
            
            return sanitized_content
        except Exception as exc:
            logger.error(f"[NeuralRewriter] Lỗi viết lại: {exc}", exc_info=True)
            err_msg = f"❌ Lỗi Neural Creative: {str(exc)[:100]}"
            await self._emit_progress(campaign_id, err_msg, status="FAILED")
            return content

# Heritage Backdoor for functional calls
async def run_neural_rewrite(
    content: str, topic: str = "", feedback: str = "", 
    campaign_id: str = "adhoc", content_type: str = "article",
    metadata: Optional[Dict[str, object]] = None,
    user_note: Optional[str] = None
) -> str:
    rewriter = NeuralRewriter()
    return await rewriter.chat(
        None, 
        content=content, 
        topic=topic, 
        feedback=feedback, 
        campaign_id=campaign_id, 
        content_type=content_type, 
        metadata=metadata, 
        user_note=user_note
    )
