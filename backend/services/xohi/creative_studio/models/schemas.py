from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Union, Optional, TypedDict
from typing_extensions import NotRequired

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

class AgentResponse(BaseModel):
    model_config = ConfigDict(strict=False)  # R105 exception: data wraps arbitrary dict
    signal: AgentSignal
    message: str
    data: Optional[Dict[str, object]] = None

class TopicSeed(BaseModel):
    model_config = ConfigDict(strict=False)  # R105: Guarded validation (lenient for LLM stability)
    title: str = Field(description="Tiêu đề bài viết thu hút, chuẩn viral")
    primary_keyword: str = Field(description="Từ khóa chính quan trọng nhất")
    secondary_keywords: List[str] = Field(description="Danh sách 3-5 từ khóa phụ bổ trợ")
    persona: str = Field(description="Mô tả phong cách viết bài (e.g. trẻ trung, chuyên gia)")
    description: str = Field(description="Mô tả tóm tắt chuẩn SEO cho bài viết (Meta Description)")
    category: CategoryEnum = Field(default=CategoryEnum.TIN_TUC, description="Phân loại danh mục bài viết (Tin tức hoặc Chính sách)")
    ground_truth: Optional[str] = Field(default=None, description="Tóm tắt bối cảnh thực tế trinh sát được từ Google (Phase 15.1)")
    creation_config: Dict[str, object] = Field(
        default_factory=lambda: {
            "style": "Viral",
            "word_count": 500,
            "max_assets": 10,
            "max_sections": 3
        },
        description="Cấu hình luồng sáng tạo mặc định"
    )

class OutlineSection(BaseModel):
    model_config = ConfigDict(strict=True)
    heading: str = Field(description="Tiêu đề mục (bắt đầu bằng H2: hoặc H3:)")
    content: str = Field(description="Mô tả nội dung chi tiết và vị trí [IMAGE_X]")

class ArticleOutline(BaseModel):
    model_config = ConfigDict(strict=False)  # R105: Guarded validation (lenient for LLM stability)
    sections: List[OutlineSection] = Field(description="Danh sách các H2, H3 và mô tả nội dung kèm vị trí chèn ảnh [IMAGE_X]")

class VisualSearchPlan(BaseModel):
    model_config = ConfigDict(strict=True)
    queries: List[str] = Field(description="List of 3-5 high-quality Google Image search queries (English preferred for professional stock quality)")

class AiAnnotation(BaseModel):
    model_config = ConfigDict(strict=True)
    type: str      # "search_intent" | "eeat_missing" | "geo_stats" | "ai_overview" | "snippet_ready" | "entity_gap" | "geo_fluff" | "citation_weak" | "geo_quotes"
    text: str      # Exact substring from the article to highlight
    message: str   # Vietnamese tip shown in tooltip
    severity: str  # "high" | "warning" | "info"

class AiReadyReport(BaseModel):
    model_config = ConfigDict(strict=True)
    geo_score: int
    summary: str
    ai_annotations: List[AiAnnotation] = Field(default_factory=list)

class AutoFixResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    old_text: str
    new_text: str

class BulkFixRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    category: str      # "copyright" | "seo" | "ai"
    annotations: List[Dict[str, object]]

class BulkFixResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    new_content: str

# ══════════════════════════════════════════════════════════════
# ANALYSIS & ENRICHMENT SCHEMAS — 2026 Edition
# ══════════════════════════════════════════════════════════════

class EnrichmentItem(BaseModel):
    model_config = ConfigDict(strict=False)
    type: str       # "stat" | "quote" | "table"
    location: str   # Where it was injected
    content: str    # The actual HTML injected

class EnrichResponse(BaseModel):
    model_config = ConfigDict(strict=False)
    new_content: str
    items: List[EnrichmentItem]
    stats_added: int
    quotes_added: int
    tables_added: int
    seo_boost_estimate: int

class CopyrightAnnotation(BaseModel):
    model_config = ConfigDict(strict=True)
    text: str           # Exact text fragment from the article
    reason: str         # Why this is risky
    source_url: str     # Competitor URL
    severity: str       # "low" | "medium" | "high"
    type: Optional[str] = "external"

class PlagiarismResult(BaseModel):
    model_config = ConfigDict(strict=True)
    uniqueness_score: float
    risk_level: str
    flagged_sentences: List[str]
    annotations: List[CopyrightAnnotation]
    similar_sources: List[str]
    verdict: str

class SeoAnnotation(BaseModel):
    model_config = ConfigDict(strict=True)
    type: str # "missing_h1", "keyword_missing", etc
    text: str
    message: str
    severity: str

class SeoSignal(BaseModel):
    model_config = ConfigDict(strict=True)
    label: str
    score: int
    status: str # "good", "warning", "error"

class SeoReport(BaseModel):
    model_config = ConfigDict(strict=True)
    total_score: int
    grade: str
    signals: List[SeoSignal]
    summary: str
    quick_wins: List[str]
    seo_annotations: List[SeoAnnotation]

class MediaAnalysisResult(BaseModel):
    model_config = ConfigDict(strict=True)
    alt_text: str = Field(description="Mô tả ảnh ngắn gọn, chuẩn SEO (không dùng từ 'hình ảnh', 'ảnh')")
    tags: List[str] = Field(description="Danh sách 5-8 từ khóa mô tả đối tượng, bối cảnh, màu sắc trong ảnh")
    description: str = Field(description="Mô tả chi tiết nội dung ảnh phục vụ AI accessibility")
    sentiment: str = Field(description="Cảm xúc chủ đạo của ảnh (e.g. chuyên nghiệp, năng động, tĩnh lặng)")
    focal_point: Optional[Dict[str, float]] = Field(
        default=None,
        description="Toạ độ điểm quan quan trọng nhất {x, y} tỷ lệ từ 0-1 để Smart Crop"
    )

class MediaAsset(BaseModel):
    model_config = ConfigDict(strict=False)
    id: str = Field(default_factory=lambda: "img_" + safe_id(), description="ID duy nhất của ảnh")
    url: str = Field(description="URL truy cập ảnh (Blob hoặc S3)")
    is_primary: bool = Field(default=False, description="Xác định đây là ảnh chính")
    order_index: int = Field(default=0, description="Thứ tự hiển thị (0 là đầu tiên)")
    media_metadata: Dict[str, object] = Field(default_factory=dict, description="Thông tin bổ sung (size, type, v.v.)")

class MediaReorderRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    asset_ids: List[str] = Field(description="Danh sách ID ảnh theo thứ tự mới")
    primary_id: Optional[str] = Field(default=None, description="ID của ảnh được chọn làm ảnh chính mới")

class CreativeCampaignState(BaseModel):
    model_config = ConfigDict(strict=False)
    campaign_id: str
    step: int = Field(default=2)
    assets: List[MediaAsset] = Field(default_factory=list)

def safe_id() -> str:
    import uuid
    return uuid.uuid4().hex[:8]

# ══════════════════════════════════════════════════════════════
# TYPEDDICTS — Strict Neural Data (Phase 82.25 Martial Law)
# ══════════════════════════════════════════════════════════════

class AnalysisCacheEntry(TypedDict):
    hash: str
    data: Dict[str, object]
    at: str

class AnalysisMetrics(TypedDict):
    unique_score: NotRequired[float]
    copyright_risk: NotRequired[str]
    seo_score: NotRequired[int]
    seo_grade: NotRequired[str]
    ai_ready_score: NotRequired[int]
    last_analyzed: NotRequired[str]

class GoldMetadata(TypedDict):
    creation_config: NotRequired[Dict[str, object]]
    analysis_cache: NotRequired[Dict[str, AnalysisCacheEntry]]
    analysis_metrics: NotRequired[AnalysisMetrics]
    avatar: NotRequired[str]
    selected_index: NotRequired[int]
    reserve_assets: NotRequired[List[object]]
    # Add other fields as discovered in the codebase
