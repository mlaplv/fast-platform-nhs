from typing import Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from backend.database.models.system import ReviewEntityType

# Strict Union type cho dynamic attributes và attachments — thậy thế 'object' wildcard
ReviewAttributeValue = Union[str, int, float, bool]
ReviewAttachment = dict[str, Union[str, int, bool]]

class CreateReviewRequest(BaseModel):
    """Payload tạo Review đa hình từ Client."""
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    
    entity_type: ReviewEntityType
    entity_id: str
    customer_name: str = Field(..., max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_location: Optional[str] = Field(None, max_length=255)
    rating: int = Field(..., ge=1, le=5)
    content: str = Field(..., min_length=5, max_length=5000)
    attributes: Optional[dict[str, ReviewAttributeValue]] = Field(None, description="Dynamic attributes like 'Thấm thấu', 'Mùi hương'")
    attachments: Optional[list[ReviewAttachment]] = Field(None, description="Media attachments URL and type")
    website_url: Optional[str] = Field(None, description="Honeypot field for bot detection")

class UpdateReviewStatusRequest(BaseModel):
    """Payload Admin cập nhật trạng thái Review."""
    model_config = ConfigDict(extra='forbid')
    
    status: str = Field(..., pattern="^(PENDING|APPROVED|REJECTED)$")

class UpdateReviewRequest(BaseModel):
    """Payload Admin chỉnh sửa nội dung Review."""
    model_config = ConfigDict(extra='forbid')
    
    content: Optional[str] = Field(None, min_length=5, max_length=15000)
    attachments: Optional[list[ReviewAttachment]] = Field(None, description="Media attachments URL and type")
    entity_type: Optional[ReviewEntityType] = None
    entity_id: Optional[str] = None
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_location: Optional[str] = Field(None, max_length=255)
    rating: Optional[int] = Field(None, ge=1, le=5)

class ReviewResponse(BaseModel):
    """Payload trả về thông tin Review."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    entity_type: ReviewEntityType
    entity_id: str
    customer_name: str
    customer_phone: Optional[str]
    customer_location: Optional[str]
    rating: int
    content: str
    attributes: Optional[dict[str, ReviewAttributeValue]]
    attachments: Optional[list[ReviewAttachment]]
    likes_count: int
    status: str
    created_at: datetime
    updated_at: datetime

class PublicReviewResponse(BaseModel):
    """Payload tinh gọn trả về thông tin Review ở Public Storefront (Bảo mật PII & Tối ưu RAM)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    customer_name: str
    customer_location: Optional[str]
    rating: int
    content: str
    attributes: Optional[dict[str, ReviewAttributeValue]]
    attachments: Optional[list[ReviewAttachment]]
    likes_count: int
    created_at: datetime

class ReviewStatsResponse(BaseModel):
    """Payload thống kê Review."""
    total_count: int
    average_rating: float
    rating_breakdown: dict[int, int]  # {5: 425, 4: 19, ...}
    has_content_count: int
    has_media_count: int
    order_count: int = 0
    attribute_summary: Optional[dict[str, dict[str, int]]] = None
    """Dict[attribute_name, Dict[value, count]] — e.g. {'Thấm thấu': {'Tốt': 87, 'Rất tốt': 12}}
    Phục vụ Copyright Analyst lấy Social Proof thực tế từ khách hàng.
    """


class AiSeedReviewRequest(BaseModel):
    """
    Extensible AI Seeding Request.
    entity_type cho phép mở rộng sang NEWS / CATEGORY sau này
    mà không cần đổi schema — chỉ thêm branch xử lý ở service.
    """
    model_config = ConfigDict(extra='forbid')

    entity_type: Literal["PRODUCT", "NEWS", "CATEGORY"] = Field(
        default="PRODUCT",
        description="Loại entity cần seeding review"
    )
    entity_id: str = Field(..., description="ID của entity (product_id / news_id / category_id)")
