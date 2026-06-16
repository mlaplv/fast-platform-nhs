from pydantic import BaseModel, Field
from typing import Optional, List
from backend.services.video_marketing.script_generator_service import VideoScriptModel

class GenerateScriptRequest(BaseModel):
    product_id: str = Field(..., description="ID sản phẩm, slug sản phẩm hoặc URL sản phẩm trong database")
    style_id: str = Field(..., description="ID phong cách video (ví dụ: tiktok_drama)")

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

