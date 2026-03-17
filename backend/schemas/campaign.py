from pydantic import BaseModel, Field, ConfigDict, AliasGenerator
from pydantic.alias_generators import to_camel
from typing import List, Dict, Optional, Union
from enum import Enum
from datetime import datetime
import uuid

# Elite V2.2: Standardized Config for Zero-Hydration & CamelCase
ELITE_CONFIG = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    alias_generator=AliasGenerator(
        serialization_alias=to_camel,
    )
)

def safe_id() -> str:
    return uuid.uuid4().hex[:8]

class AgentSignal(str, Enum):
    PROCEED_NEXT = "PROCEED_NEXT"
    REDO_PREVIOUS = "REDO_PREVIOUS"
    FAIL_GRACEFULLY = "FAIL_GRACEFULLY"

class CategoryEnum(str, Enum):
    TIN_TUC = "Tin tức"
    CHINH_SACH = "Chính sách"

class CampaignCategory(str, Enum):
    CREATIVE_CONTENT = "CREATIVE_CONTENT"
    AD_MANAGEMENT = "AD_MANAGEMENT"

class CampaignStep(BaseModel):
    model_config = ELITE_CONFIG
    step_number: int
    name: str
    status: str = "PENDING"
    result: Optional[Dict[str, object]] = None
    agent_msg: Optional[str] = None
    retry_count: int = 0

class ContentCampaign(BaseModel):
    model_config = ELITE_CONFIG

    id: str
    user_id: Optional[str] = None
    source_input: Optional[str] = ""
    reviewer_type: str = "ADMIN_MANUAL"
    current_step: int = 1
    status: str = "WAITING_FOR_REVIEW"
    gold_metadata: Optional[Dict[str, object]] = Field(default_factory=dict)
    topic_data: Optional[Dict[str, object]] = Field(default_factory=dict)
    assets_data: Optional[List[MediaAsset]] = Field(default_factory=list)
    outline_data: Optional[Dict[str, object]] = Field(default_factory=dict)
    draft_content: Optional[str] = None
    final_html: Optional[str] = None
    search_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)

class AgentResponse(BaseModel):
    model_config = ELITE_CONFIG
    signal: AgentSignal
    data: Optional[Dict[str, object]] = None
    message: Optional[str] = None

class TopicSeed(BaseModel):
    model_config = ELITE_CONFIG
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

class OutlineSection(BaseModel):
    model_config = ELITE_CONFIG
    heading: str = Field(description="Tiêu đề mục (bắt đầu bằng H2: hoặc H3:)")
    content: str = Field(description="Mô tả nội dung chi tiết và vị trí [IMAGE_X]")

class ArticleOutline(BaseModel):
    model_config = ELITE_CONFIG
    sections: List[OutlineSection] = Field(description="Danh sách các H2, H3 và mô tả nội dung kèm vị trí chèn ảnh [IMAGE_X]")

class VisualSearchPlan(BaseModel):
    model_config = ELITE_CONFIG
    queries: List[str] = Field(description="List of 3-5 high-quality Google Image search queries (English preferred for professional stock quality)")

class AiAnnotation(BaseModel):
    model_config = ELITE_CONFIG
    type: str      # "geo_stats" | "geo_quotes" | "geo_fluff" | "geo_snippet"
    text: str      # Exact substring from the article to highlight
    message: str   # Vietnamese tip shown in tooltip
    severity: str  # "high" | "warning" | "info"

class AiReadyReport(BaseModel):
    model_config = ELITE_CONFIG
    geo_score: int
    summary: str
    ai_annotations: List[AiAnnotation] = Field(default_factory=list)

class AutoFixResponse(BaseModel):
    model_config = ELITE_CONFIG
    old_text: str
    new_text: str

class BulkFixRequest(BaseModel):
    model_config = ELITE_CONFIG
    category: str      # "copyright" | "seo" | "ai"
    annotations: List[Dict[str, object]]

class BulkFixResponse(BaseModel):
    model_config = ELITE_CONFIG
    new_content: str

class MediaAnalysisResult(BaseModel):
    model_config = ELITE_CONFIG
    alt_text: str = Field(description="Mô tả ảnh ngắn gọn, chuẩn SEO (không dùng từ 'hình ảnh', 'ảnh')")
    tags: List[str] = Field(description="Danh sách 5-8 từ khóa mô tả đối tượng, bối cảnh, màu sắc trong ảnh")
    description: str = Field(description="Mô tả chi tiết nội dung ảnh phục vụ AI accessibility")
    sentiment: str = Field(description="Cảm xúc chủ đạo của ảnh (e.g. chuyên nghiệp, năng động, tĩnh lặng)")
    focal_point: Optional[Dict[str, float]] = Field(
        default=None,
        description="Toạ độ điểm quan quan trọng nhất {x, y} tỷ lệ từ 0-1 để Smart Crop"
    )

class MediaAsset(BaseModel):
    """Phase 15.3: Standard Media Asset for Campaigns (CamelCase)"""
    model_config = ELITE_CONFIG
    id: str = Field(default_factory=lambda: "img_" + safe_id(), description="ID duy nhất của ảnh")
    file_path: str = Field(validation_alias="url", description="Path/URL của ảnh")
    is_primary: bool = Field(default=False, description="Xác định đây là ảnh chính")
    order_index: int = Field(default=0, description="Thứ tự hiển thị (0 là đầu tiên)")
    media_metadata: Dict[str, object] = Field(default_factory=dict, description="Thông tin bổ sung (size, type, v.v.)")

class MediaReorderRequest(BaseModel):
    model_config = ELITE_CONFIG
    asset_ids: List[str] = Field(description="Danh sách ID ảnh theo thứ tự mới")
    primary_id: Optional[str] = Field(default=None, description="ID của ảnh được chọn làm ảnh chính mới")

class CreativeCampaignState(BaseModel):
    model_config = ELITE_CONFIG
    campaign_id: str
    step: int = Field(default=2)
    assets: List[MediaAsset] = Field(default_factory=list)

class CampaignListItem(BaseModel):
    model_config = ELITE_CONFIG
    id: str
    topic_data: Optional[Dict[str, object]] = None
    status: str
    current_step: int
    created_at: datetime
    user_id: Optional[str] = None
    category: Optional[str] = None

class CampaignListResponse(BaseModel):
    model_config = ELITE_CONFIG
    items: List[CampaignListItem]
    total: int
    has_more: bool
    limit: int
    offset: int

class GenericResponse(BaseModel):
    model_config = ELITE_CONFIG
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, object]] = None

# Explicit model rebuild (R106)
ContentCampaign.model_rebuild()
AgentResponse.model_rebuild()
GenericResponse.model_rebuild()
TopicSeed.model_rebuild()
ArticleOutline.model_rebuild()
CreativeCampaignState.model_rebuild()
