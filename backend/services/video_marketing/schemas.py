from pydantic import BaseModel, Field
from typing import Optional, List
from backend.services.video_marketing.script_generator_service import VideoScriptModel

class CompetitorAnalysisInput(BaseModel):
    competitor_weaknesses: List[str] = Field(..., description="Danh sách điểm yếu lớn của đối thủ")
    our_strengths: List[str] = Field(..., description="Danh sách điểm mạnh nổi trội của ta")
    core_message: str = Field(..., description="Thông điệp cốt lõi đắt giá nhất")

class EvaluationCriterion(BaseModel):
    score: int = Field(..., description="Điểm số đánh giá từ 1 đến 10")
    pros: List[str] = Field(..., description="Các điểm làm tốt (đúng chuẩn)")
    cons: List[str] = Field(..., description="Các lỗi kỹ thuật kịch bản (cần sửa)")
    suggestions: List[str] = Field(..., description="Đề xuất viết lại/chỉnh sửa cụ thể")

class ScriptEvaluationReport(BaseModel):
    hook_retention: EvaluationCriterion = Field(..., description="Sức hút Hook 3s đầu & Khả năng giữ chân người xem")
    audio_visual_harmony: EvaluationCriterion = Field(..., description="Độ đồng bộ nghe - nhìn (Thời lượng thoại vs Visual Pacing)")
    ai_generation_viability: EvaluationCriterion = Field(..., description="Độ khả thi khi sinh video bằng Runway/Midjourney (Tránh từ trừu tượng)")
    platform_optimization: EvaluationCriterion = Field(..., description="Độ tối ưu hóa theo định dạng và thuật toán nền tảng")
    brand_integrity: EvaluationCriterion = Field(..., description="Tính bảo toàn nhận diện bao bì & logo sản phẩm")
    duration_compliance: EvaluationCriterion = Field(..., description="Độ tuân thủ thời lượng mục tiêu (sai số tối đa 10% so với target_duration)")
    emotional_arc: EvaluationCriterion = Field(..., description="Kiến trúc cảm xúc: Hành trình HOOK → Pain → Solution → Proof → CTA có mạch lạc, tăng tiến không?")
    cta_effectiveness: EvaluationCriterion = Field(..., description="Hiệu quả CTA: Lời kêu gọi hành động có rõ ràng, cấp bách, dễ thực hiện ngay không?")
    tts_sync_compliance: EvaluationCriterion = Field(..., description="Kiểm tra word-per-second từng phân cảnh: Voiceover có khả thi để đọc trong thời gian quy định (2.5-3.5 từ/giây)?")
    overall_score: float = Field(..., description="Điểm trung bình tổng hợp của toàn bộ kịch bản (scale 1-10, 1 chữ số thập phân)")
    overall_recommendation: str = Field(..., description="Định hướng chiến lược tổng quan của Đạo diễn AI")

class GenerateScriptRequest(BaseModel):
    source_type: str = Field("product", description="Loại nguồn đầu vào: product, article, hoặc custom")
    product_id: Optional[str] = Field(None, description="ID sản phẩm nếu source_type là product")
    article_id: Optional[str] = Field(None, description="ID bài viết nếu source_type là article")
    description: Optional[str] = Field(None, description="Mô tả tự do nếu source_type là custom")
    style_id: str = Field(..., description="ID phong cách video (ví dụ: tiktok_drama)")
    aspect_ratio: Optional[str] = Field("9:16", description="Tỷ lệ khung hình: 16:9 (ngang) hoặc 9:16 (dọc)")
    target_duration: Optional[int] = Field(30, description="Thời lượng mục tiêu của video tính bằng giây")
    competitor_analysis: Optional[CompetitorAnalysisInput] = Field(None, description="Thông tin đối thủ cạnh tranh và USP đã phân tích trước đó")
    extra_requirements: Optional[str] = Field(None, description="Yêu cầu thêm quan trọng: bối cảnh, nhân vật, phong cách hình ảnh, quy tắc đặc biệt mà AI phải tuân theo bắt buộc")

class CreateStyleRequest(BaseModel):
    id: str = Field(..., description="Mã phong cách viết (slug, ví dụ: tiktok_trend_2026)")
    name: str = Field(..., description="Tên phong cách hiển thị")
    platform: str = Field(..., description="Kênh hỗ trợ (TikTok, YouTube, Reels...)")
    hook_template: str = Field(..., description="Hướng dẫn thiết kế hook 3s đầu")
    style_instruction: str = Field(..., description="Chỉ dẫn chi tiết phong cách kịch bản cho AI")
    is_active: bool = Field(True, description="Trạng thái hoạt động")

class VideoScriptResponse(BaseModel):
    id: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    style_id: str
    style_name: Optional[str] = None
    style_platform: Optional[str] = None
    title: str
    structured_script: VideoScriptModel
    created_at: str

class UpdateScriptRequest(BaseModel):
    title: Optional[str] = Field(None, description="Tiêu đề cập nhật của kịch bản")
    structured_script: Optional[VideoScriptModel] = Field(None, description="Cấu trúc kịch bản cập nhật đầy đủ")

class VideoScriptListResponse(BaseModel):
    data: List[VideoScriptResponse]
    total: int

class VideoStyleResponse(BaseModel):
    id: str
    name: str
    platform: str
    hook_template: str
    style_instruction: str
    is_active: bool

