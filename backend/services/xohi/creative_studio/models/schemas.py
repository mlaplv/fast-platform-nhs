from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Union, Optional

class AgentSignal(str, Enum):
    PROCEED_NEXT = "PROCEED_NEXT"
    REDO_PREVIOUS = "REDO_PREVIOUS"
    FAIL_GRACEFULLY = "FAIL_GRACEFULLY"

class CategoryEnum(str, Enum):
    TIN_TUC = "Tin tức"
    CHINH_SACH = "Chính sách"

class AgentResponse(BaseModel):
    signal: AgentSignal
    message: str
    data: Optional[Dict[str, object]] = None
    # NOTE: strict=True intentionally omitted — data wraps arbitrary dict by design (R105 exception)

class TopicSeed(BaseModel):
    title: str = Field(description="Tiêu đề bài viết thu hút, chuẩn viral")
    primary_keyword: str = Field(description="Từ khóa chính quan trọng nhất")
    secondary_keywords: List[str] = Field(description="Danh sách 3-5 từ khóa phụ bổ trợ")
    persona: str = Field(description="Mô tả phong cách viết bài (e.g. trẻ trung, chuyên gia)")
    description: str = Field(description="Mô tả tóm tắt chuẩn SEO cho bài viết (Meta Description)")
    category: CategoryEnum = Field(default=CategoryEnum.TIN_TUC, description="Phân loại danh mục bài viết (Tin tức hoặc Chính sách)")
    creation_config: Dict[str, object] = Field(
        default_factory=lambda: {
            "style": "Chuyên nghiệp",
            "word_count": 500,
            "max_assets": 10,
            "max_sections": 3
        },
        description="Cấu hình luồng sáng tạo mặc định"
    )

    model_config = ConfigDict(strict=False)  # R105: Guarded validation (lenient for LLM stability)

class OutlineSection(BaseModel):
    heading: str = Field(description="Tiêu đề mục (bắt đầu bằng H2: hoặc H3:)")
    content: str = Field(description="Mô tả nội dung chi tiết và vị trí [IMAGE_X]")

class ArticleOutline(BaseModel):
    sections: List[OutlineSection] = Field(description="Danh sách các H2, H3 và mô tả nội dung kèm vị trí chèn ảnh [IMAGE_X]")

    model_config = ConfigDict(strict=False)  # R105: Guarded validation (lenient for LLM stability)

class VisualSearchPlan(BaseModel):
    queries: List[str] = Field(description="List of 3-5 high-quality Google Image search queries (English preferred for professional stock quality)")

class AiAnnotation(BaseModel):
    type: str      # "geo_stats" | "geo_quotes" | "geo_fluff" | "geo_snippet"
    text: str      # Exact substring from the article to highlight
    message: str   # Vietnamese tip shown in tooltip
    severity: str  # "high" | "warning" | "info"

class AiReadyReport(BaseModel):
    geo_score: int
    summary: str
    ai_annotations: List[AiAnnotation] = Field(default_factory=list)

class AutoFixResponse(BaseModel):
    old_text: str
    new_text: str

class BulkFixRequest(BaseModel):
    category: str      # "copyright" | "seo" | "ai"
    annotations: List[Dict[str, object]]

class BulkFixResponse(BaseModel):
    new_content: str

class MediaAsset(BaseModel):
    id: str = Field(default_factory=lambda: "img_" + safe_id(), description="ID duy nhất của ảnh")
    url: str = Field(description="URL truy cập ảnh (Blob hoặc S3)")
    is_primary: bool = Field(default=False, description="Xác định đây là ảnh chính")
    order_index: int = Field(default=0, description="Thứ tự hiển thị (0 là đầu tiên)")
    metadata: Dict[str, object] = Field(default_factory=dict, description="Thông tin bổ sung (size, type, v.v.)")

    model_config = ConfigDict(strict=False)

class MediaReorderRequest(BaseModel):
    asset_ids: List[str] = Field(description="Danh sách ID ảnh theo thứ tự mới")
    primary_id: Optional[str] = Field(default=None, description="ID của ảnh được chọn làm ảnh chính mới")

class CreativeCampaignState(BaseModel):
    campaign_id: str
    step: int = Field(default=2)
    assets: List[MediaAsset] = Field(default_factory=list)

    model_config = ConfigDict(strict=False)

def safe_id() -> str:
    import uuid
    return uuid.uuid4().hex[:8]
