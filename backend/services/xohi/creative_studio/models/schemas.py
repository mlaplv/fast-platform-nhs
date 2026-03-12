from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

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
    data: Optional[Dict[str, Any]] = None
    # NOTE: strict=True intentionally omitted — data wraps arbitrary dict by design (R105 exception)

class TopicSeed(BaseModel):
    title: str = Field(description="Tiêu đề bài viết thu hút, chuẩn viral")
    primary_keyword: str = Field(description="Từ khóa chính quan trọng nhất")
    secondary_keywords: List[str] = Field(description="Danh sách 3-5 từ khóa phụ bổ trợ")
    persona: str = Field(description="Mô tả phong cách viết bài (e.g. trẻ trung, chuyên gia)")
    description: str = Field(description="Mô tả tóm tắt chuẩn SEO cho bài viết (Meta Description)")
    category: CategoryEnum = Field(default=CategoryEnum.TIN_TUC, description="Phân loại danh mục bài viết (Tin tức hoặc Chính sách)")
    creation_config: Dict[str, Any] = Field(
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

class BulkFixRequest(BaseModel):
    category: str      # "copyright" | "seo" | "ai"
    annotations: List[Dict[str, Any]]

class BulkFixResponse(BaseModel):
    new_content: str

