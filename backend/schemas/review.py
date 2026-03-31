from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from backend.database.models.system import ReviewEntityType

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

class UpdateReviewStatusRequest(BaseModel):
    """Payload Admin cập nhật trạng thái Review."""
    model_config = ConfigDict(extra='forbid')
    
    status: str = Field(..., pattern="^(PENDING|APPROVED|REJECTED)$")

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
    status: str
    created_at: datetime
    updated_at: datetime
