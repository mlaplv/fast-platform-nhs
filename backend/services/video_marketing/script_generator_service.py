from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.schema import PromptComponent, PromptCategory
from backend.services.video_marketing.prompts_registrar import register_video_prompts
from backend.database.models.video_marketing import VideoScriptStyle

logger = logging.getLogger("api-gateway")

# ── Pydantic V2 Models ────────────────────────────────────────────────────────

class SceneModel(BaseModel):
    scene_number: int = Field(..., description="Số thứ tự phân cảnh (bắt đầu từ 1)")
    visual_description: str = Field(..., description="Mô tả chi tiết hình ảnh hiển thị trên màn hình, bao gồm góc máy, hành động của nhân vật")
    voiceover: str = Field(..., description="Lời thoại thuyết minh bằng tiếng Việt, súc tích, nhịp điệu sinh động và thuyết phục")
    duration: float = Field(..., description="Thời lượng phân cảnh tính bằng giây (từ 2.0 đến 7.0)")
    audio_cue: Optional[str] = Field(None, description="Mô tả nhạc nền (BGM) hoặc hiệu ứng âm thanh (SFX) ở cảnh này")
    image_prompt: Optional[str] = Field(None, description="Mô tả chi tiết hình ảnh bằng tiếng Việt (thuần Việt 100%) để làm Prompt tạo hình ảnh/cảnh nền AI")
    image_url: Optional[str] = Field(None, description="Đường dẫn hình ảnh đã gán cho cảnh (nếu có)")
    scene_notes: Optional[str] = Field(None, description="Ghi chú đạo diễn dành riêng cho cảnh này")

class VideoScriptModel(BaseModel):
    title: str = Field(..., description="Tiêu đề gợi ý của video marketing hoặc tên chiến dịch")
    style_name: str = Field(..., description="Tên phong cách/xu hướng video được áp dụng")
    target_audience: str = Field(..., description="Mô tả tóm tắt đối tượng khách hàng mục tiêu của video")
    notes: Optional[str] = Field(None, description="Ghi chú tổng quan của kịch bản video")
    scenes: List[SceneModel] = Field(..., description="Danh sách các phân cảnh tạo nên video")
    total_duration: float = Field(..., description="Tổng thời lượng ước tính của cả video (bằng tổng thời lượng các cảnh)")

# ── Service Class ─────────────────────────────────────────────────────────────

class ScriptGeneratorService:
    """AI Service sinh kịch bản video marketing sử dụng TrinityBridge và NPO Vault."""

    def __init__(self) -> None:
        # Tự động đăng ký các prompt cơ bản nếu chưa được đăng ký trong composer
        if "video_script_generation" not in composer._templates:
            register_video_prompts()
        
        # Khởi tạo Agent PydanticAI để ép cấu trúc kịch bản
        self.agent = Agent(
            output_type=VideoScriptModel,
            retries=3
        )

    async def generate_script(self, product_context: str, style_id: str, db: AsyncSession) -> VideoScriptModel:
        """
        Sinh kịch bản video từ ngữ cảnh sản phẩm và phong cách (style_id) được chọn.
        """
        logger.info(f"[ScriptGenerator] Fetching style instructions for: {style_id}")
        
        # 1. Lấy phong cách kịch bản từ database
        stmt = select(VideoScriptStyle).where(VideoScriptStyle.id == style_id).where(VideoScriptStyle.is_active == True)
        res = await db.execute(stmt)
        style = res.scalar_one_or_none()
        
        if not style:
            # Fallback nếu không tìm thấy style cụ thể
            logger.warning(f"[ScriptGenerator] Style '{style_id}' not found. Using default instructions.")
            style_instruction = "Viết kịch bản video ngắn, nhanh, hiện đại."
            hook_template = "3 giây đầu tiên kích thích sự tò mò."
            style_name = "Mặc định"
        else:
            style_instruction = style.style_instruction
            hook_template = style.hook_template
            style_name = style.name

        # 2. Đăng ký dynamic Prompt Component cho style được chọn
        style_comp_id = f"video_style_{style_id}"
        style_comp = PromptComponent(
            id=style_comp_id,
            category=PromptCategory.AGENT,  # Đăng ký dưới dạng AGENT để PromptComposer ghép nối bình thường
            content=f"""[STYLE INSTRUCTIONS: {style_name}]
{style_instruction}

[HOOK DESIGN]
{hook_template}"""
        )
        composer.register_component(style_comp)

        # 3. Lắp ráp Prompt động qua PromptComposer
        system_prompt = composer.compose("video_script_generation", extra_components=[style_comp_id])
        
        # 4. Gửi request AI qua TrinityBridge để tự động xoay key và chống rate limit
        logger.info("[ScriptGenerator] Sending prompt to TrinityBridge...")
        script_data = await trinity_bridge.run(
            agent=self.agent,
            prompt=product_context,
            system_prompt=system_prompt,
            role="brain"  # Ưu tiên các model thông minh (Gemini 1.5 Pro / Flash)
        )
        
        # TrinityBridge.run trả về đối tượng dữ liệu khớp với result_type của Agent (VideoScriptModel)
        if isinstance(script_data, VideoScriptModel):
            return script_data
        elif isinstance(script_data, dict):
            return VideoScriptModel(**script_data)
        else:
            # Dự phòng nếu trả về kiểu dữ liệu khác
            logger.error(f"[ScriptGenerator] Unexpected return type from TrinityBridge: {type(script_data)}")
            raise ValueError("Không thể sinh định dạng kịch bản chuẩn.")

script_generator_service = ScriptGeneratorService()
