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
    
    # model_config = ConfigDict(strict=True) removed for AI output flexibility

class TopicSeed(BaseModel):
    title: str = Field(description="Tiêu đề bài viết thu hút, chuẩn viral")
    primary_keyword: str = Field(description="Từ khóa chính quan trọng nhất")
    secondary_keywords: List[str] = Field(description="Danh sách 3-5 từ khóa phụ bổ trợ")
    persona: str = Field(description="Mô tả phong cách viết bài (e.g. trẻ trung, chuyên gia)")
    description: str = Field(description="Mô tả tóm tắt chuẩn SEO cho bài viết (Meta Description)")
    category: CategoryEnum = Field(default=CategoryEnum.TIN_TUC, description="Phân loại danh mục bài viết (Tin tức hoặc Chính sách)")
    
    # model_config = ConfigDict(strict=True) # R105: Security against Data Poisoning

class ArticleOutline(BaseModel):
    sections: List[Dict[str, str]] = Field(description="Danh sách các H2, H3 và mô tả nội dung kèm vị trí chèn ảnh [IMAGE_X]")
    
    # model_config = ConfigDict(strict=True)
