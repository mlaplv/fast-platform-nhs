from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from contextvars import ContextVar

from pydantic_ai import Agent
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.services.xohi.prompts import composer
from backend.services.xohi.prompts.schema import PromptComponent, PromptCategory
from backend.services.video_marketing.prompts_registrar import register_video_prompts
from backend.database.models.video_marketing import VideoScriptStyle

logger = logging.getLogger("api-gateway")

strict_duration_var: ContextVar[bool] = ContextVar("strict_duration", default=False)

# ── Pydantic V2 Models ────────────────────────────────────────────────────────

class SceneModel(BaseModel):
    scene_number: int = Field(..., description="Số thứ tự phân cảnh (bắt đầu từ 1)")
    visual_description: str = Field(..., description="Mô tả chi tiết hình ảnh hiển thị trên màn hình, bao gồm góc máy, hành động của nhân vật")
    voiceover: str = Field(..., description="Lời thoại thuyết minh bằng tiếng Việt, súc tích, nhịp điệu sinh động và thuyết phục")
    duration: float = Field(..., description="Thời lượng phân cảnh tính bằng giây (từ 2.0 đến 7.0)")
    scene_notes: Optional[str] = Field(None, description="Ghi chú đạo diễn dành riêng cho cảnh này")

class LandingPageHeadlineMatch(BaseModel):
    headline: str = Field(..., description="Tiêu đề chính (H1) tối ưu hóa cho trang đích, đồng bộ với Hook của kịch bản")
    subheadline: str = Field(..., description="Tiêu đề phụ (H2) làm nổi bật giải pháp, USP của sản phẩm")
    match_psychology: str = Field(..., description="Tâm lý kích hoạt cảm xúc (ví dụ: 'Sợ hãi / Cảnh báo', 'Lợi ích tức thì', 'Tò mò/Khám phá')")

class VideoScriptModel(BaseModel):
    title: str = Field(..., description="Tiêu đề gợi ý của video marketing hoặc tên chiến dịch")
    style_name: str = Field(..., description="Tên phong cách/xu hướng video được áp dụng")
    target_audience: str = Field(..., description="Mô tả tóm tắt đối tượng khách hàng mục tiêu của video")
    notes: Optional[str] = Field(None, description="Ghi chú tổng quan của kịch bản video")
    scenes: List[SceneModel] = Field(..., description="Danh sách các phân cảnh tạo nên video")
    total_duration: float = Field(..., description="Tổng thời lượng ước tính của cả video (bằng tổng thời lượng các cảnh)")
    competitor_analysis: Optional[dict] = Field(None, description="Phân tích đối thủ cạnh tranh từ Google Search & AI")
    aspect_ratio: Optional[str] = Field(None, description="Tỷ lệ khung hình được định cấu hình")
    landing_page_headlines: Optional[List[LandingPageHeadlineMatch]] = Field(None, description="3 cặp H1 Headline & H2 Subheadline tương thích, tạo Message Match tối ưu CR trang đích")
    evaluation: Optional[dict] = Field(None, description="Báo cáo đánh giá chất lượng kịch bản từ Đạo diễn AI")
    target_duration: Optional[int] = Field(None, description="Thời lượng mục tiêu của video tính bằng giây")

    @model_validator(mode='after')
    def check_duration_compliance(self) -> 'VideoScriptModel':
        # Calculate actual total duration
        if self.scenes:
            actual_total = sum(scene.duration for scene in self.scenes)
            self.total_duration = round(actual_total, 1)
        
        if strict_duration_var.get() and self.target_duration is not None:
            # Ensure compliance within 10%
            lower_bound = self.target_duration * 0.9
            upper_bound = self.target_duration * 1.1
            if not (lower_bound <= self.total_duration <= upper_bound):
                raise ValueError(
                    f"Tổng thời lượng kịch bản ({self.total_duration}s) không tuân thủ thời lượng mục tiêu ({self.target_duration}s) trong sai số 10%. "
                    f"Vui lòng phân chia hoặc điều chỉnh thời lượng của các cảnh (scenes) hoặc thêm/bớt cảnh để tổng thời lượng thực tế của các cảnh nằm trong khoảng từ {lower_bound:.1f}s đến {upper_bound:.1f}s."
                )
        return self

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
            retries=2
        )

    async def analyze_competitors(self, name: str, description: str) -> dict:
        """
        [ELITE V2.2] Phân tích đối thủ cạnh tranh phản biện bằng Google Search & AI.
        """
        from backend.services.xohi.google_search import google_search_service
        
        # 1. Tạo câu truy vấn tìm kiếm
        search_query = f"{name} đối thủ cạnh tranh review"
        logger.info(f"[ScriptGenerator] Searching Google for competitor context: {search_query}")
        
        search_results = []
        try:
            search_results = await google_search_service.search(search_query, num=4)
        except Exception as e:
            logger.error(f"[ScriptGenerator] Google Search failed: {e}")
            
        # 2. Tổng hợp ngữ cảnh từ tìm kiếm
        search_context_str = ""
        if search_results:
            for idx, item in enumerate(search_results):
                search_context_str += f"\n[{idx+1}] {item.get('title')}\nSnippet: {item.get('snippet')}\nLink: {item.get('link')}\n"
        else:
            search_context_str = "Không tìm thấy kết quả tìm kiếm trực tiếp trên Google."

        # 3. Sử dụng AI để phân tích phản biện và trích xuất điểm yếu đối thủ & điểm mạnh của ta
        analysis_prompt = f"""
        Bạn là một chuyên gia Chiến lược Marketing AI cao cấp. 
        Hãy phân tích cạnh tranh phản biện giữa sản phẩm/chủ đề của chúng ta và các đối thủ trên thị trường dựa trên thông tin nguồn và kết quả tìm kiếm thực tế.

        [THÔNG TIN CỦA CHÚNG TA]
        Tên/Chủ đề: {name}
        Mô tả/Chi tiết: {description}

        [KẾT QUẢ TÌM KIẾM GOOGLE VỀ ĐỐI THỦ VÀ THỊ TRƯỜNG]
        {search_context_str}

        Hãy phân tích phản biện và trả về kết quả dưới định dạng JSON chính xác theo cấu trúc sau (không kèm markdown block, chỉ trả về JSON raw):
        {{
          "competitor_weaknesses": ["điểm yếu đối thủ 1", "điểm yếu đối thủ 2", "điểm yếu đối thủ 3"],
          "our_strengths": ["điểm mạnh/lợi thế cạnh tranh USP 1", "điểm mạnh 2", "điểm mạnh 3"],
          "core_message": "thông điệp cốt lõi đắt giá nhất để thuyết phục khách hàng mua hàng của ta thay vì đối thủ"
        }}
        """

        try:
            class CompetitiveAnalysisModel(BaseModel):
                competitor_weaknesses: List[str] = Field(..., description="Danh sách 3 điểm yếu lớn của đối thủ")
                our_strengths: List[str] = Field(..., description="Danh sách 3 điểm mạnh nổi trội của ta")
                core_message: str = Field(..., description="Thông điệp cốt lõi đắt giá nhất")

            analysis_agent = Agent(
                output_type=CompetitiveAnalysisModel,
                retries=2
            )
            analysis_data = await trinity_bridge.run(
                agent=analysis_agent,
                prompt=analysis_prompt,
                role="brain"
            )
            if isinstance(analysis_data, CompetitiveAnalysisModel):
                return analysis_data.model_dump()
            elif isinstance(analysis_data, dict):
                return analysis_data
        except Exception as e:
            logger.error(f"[ScriptGenerator] Competitive analysis AI run failed: {e}")
            
        # Fallback hữu ích nếu có lỗi xảy ra
        return {
            "competitor_weaknesses": [
                "Đối thủ có dịch vụ/sản phẩm chưa tối ưu hóa cho người dùng Việt Nam",
                "Chi phí vận hành và giá thành cao so với giá trị thực tế mang lại",
                "Thiếu sự nhanh nhạy, quy trình xử lý cồng kềnh mất nhiều thời gian"
            ],
            "our_strengths": [
                "Giải pháp thiết thực, tập trung giải quyết nỗi đau của khách hàng một cách trực diện",
                "Tối ưu hóa chi phí tốt nhất trên thị trường hiện nay",
                "Tính năng vượt trội, cam kết đồng hành và hỗ trợ chuyên nghiệp 24/7"
            ],
            "core_message": f"Lựa chọn {name} là giải pháp thông minh và hiệu quả vượt trội dành riêng cho bạn!"
        }

    async def generate_script(
        self,
        source_context: str,
        style: Optional[VideoScriptStyle],
        aspect_ratio: str = "9:16",
        target_duration: int = 30,
        competitor_analysis: Optional[dict] = None
    ) -> VideoScriptModel:
        """
        Sinh kịch bản video từ nguồn thông tin đã chọn, kết cấu thời lượng, khung hình và phân tích cạnh tranh.
        """
        style_id = style.id if style else "default"
        logger.info(f"[ScriptGenerator] Using style instructions for: {style_id}")
        
        if not style:
            logger.warning(f"[ScriptGenerator] Style not provided. Using default instructions.")
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
            category=PromptCategory.AGENT,
            content=f"""[STYLE INSTRUCTIONS: {style_name}]
{style_instruction}

[HOOK DESIGN]
{hook_template}"""
        )
        composer.register_component(style_comp)

        # 3. Lắp ráp Prompt động qua PromptComposer
        system_prompt = composer.compose("video_script_generation", extra_components=[style_comp_id])
        
        # 4. Tạo prompt chi tiết kết hợp cấu hình thời lượng, khung hình và phản biện đối thủ
        prompt_with_config = f"""[THÔNG IN NGUỒN PHÂN TÍCH]
{source_context}

[THÔNG SỐ KỸ THUẬT VIDEO]
- Tỷ lệ khung hình: {aspect_ratio} (định dạng layout hiển thị tương ứng)
- Thời lượng mục tiêu của video: {target_duration} giây

Yêu cầu cực kỳ quan trọng về thời lượng:
1. Bắt buộc phải điền giá trị của trường 'target_duration' trong kết quả JSON bằng đúng {target_duration}.
2. Phân chia thời lượng các cảnh (scenes) sao cho tổng thời lượng (total_duration) xấp xỉ {target_duration} giây, tuân thủ sai số không quá 10% (tức là tổng thời lượng các cảnh phải nằm trong khoảng {target_duration * 0.9}s đến {target_duration * 1.1}s).
"""

        if competitor_analysis:
            weaknesses = "\n".join([f"  + {w}" for w in competitor_analysis.get("competitor_weaknesses", [])])
            strengths = "\n".join([f"  + {s}" for s in competitor_analysis.get("our_strengths", [])])
            core_msg = competitor_analysis.get("core_message", "")
            
            prompt_with_config += f"""
[PHÂN TÍCH ĐỐI THỦ CẠNH TRANH & PHẢN BIỆN THỰC TẾ]
- Điểm yếu của đối thủ cạnh tranh trên thị trường:
{weaknesses}
- Điểm mạnh vượt trội của chúng ta (USP):
{strengths}
- Thông điệp truyền thông cốt lõi:
"{core_msg}"

YÊU CẦU BIÊN KỊCH MARKETING:
Hãy lồng ghép khéo léo thông điệp cốt lõi và các USP của chúng ta vào kịch bản (đặc biệt là trong phần lời thoại voiceover và hook 3s đầu) để so sánh/phản biện gián tiếp hoặc trực diện các điểm yếu của đối thủ, giúp khách hàng nhận thấy giá trị vượt trội của sản phẩm/bài viết của chúng ta!
"""

        # 5. Gửi request AI qua TrinityBridge
        logger.info("[ScriptGenerator] Sending structured prompt to TrinityBridge...")
        token = strict_duration_var.set(True)
        try:
            script_data = await trinity_bridge.run(
                agent=self.agent,
                prompt=prompt_with_config,
                system_prompt=system_prompt,
                role="brain",
                per_model_timeout=35.0
            )
        finally:
            strict_duration_var.reset(token)
        
        # Gán thêm dữ liệu phân tích và khung hình vào object trả về
        if isinstance(script_data, VideoScriptModel):
            script_data.competitor_analysis = competitor_analysis
            script_data.aspect_ratio = aspect_ratio
            if script_data.target_duration is None:
                script_data.target_duration = target_duration
            return script_data
        elif isinstance(script_data, dict):
            script_data["competitor_analysis"] = competitor_analysis
            script_data["aspect_ratio"] = aspect_ratio
            if "target_duration" not in script_data or script_data["target_duration"] is None:
                script_data["target_duration"] = target_duration
            return VideoScriptModel(**script_data)
        else:
            logger.error(f"[ScriptGenerator] Unexpected return type from TrinityBridge: {type(script_data)}")
            raise ValueError("Không thể sinh định dạng kịch bản chuẩn.")

script_generator_service = ScriptGeneratorService()
