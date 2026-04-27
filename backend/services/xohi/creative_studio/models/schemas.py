from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Union, Optional, TypedDict
from typing_extensions import NotRequired

class AgentSignal(str, Enum):
    PROCEED_NEXT = "PROCEED_NEXT"
    REDO_PREVIOUS = "REDO_PREVIOUS"
    FAIL_GRACEFULLY = "FAIL_GRACEFULLY"

class CategoryEnum(str, Enum):
    TIN_TUC = "Bài viết"
    CHINH_SACH = "Chính sách"

class CampaignCategory(str, Enum):
    CREATIVE_CONTENT = "CREATIVE_CONTENT"
    AD_MANAGEMENT = "AD_MANAGEMENT"
    PRODUCT_CATALOG = "PRODUCT_CATALOG"

class AgentResponse(BaseModel):
    model_config = ConfigDict(strict=False)  # R105 exception: data wraps arbitrary dict
    signal: AgentSignal
    message: str
    data: Optional[Dict[str, object]] = None

class TopicSeed(BaseModel):
    model_config = ConfigDict(strict=False)  # R105: Guarded validation (lenient for LLM stability)
    title: str = Field(description="Tiêu đề (Viral/Bài viết) hoặc Tên sản phẩm chính thức (Hàng hóa)")
    primary_keyword: str = Field(description="Từ khóa chính hoặc Tên sản phẩm cốt lõi")
    secondary_keywords: List[str] = Field(description="Danh sách từ khóa bổ trợ hoặc Thông số/Đặc tính then chốt")
    persona: str = Field(description="Mô tả phong cách (e.g. Chuyên gia review, Copywriter bán hàng)")
    description: str = Field(description="Mô tả SEO (Meta Description) hoặc Tóm tắt đặc điểm nổi bật SP")
    category: str = Field(default="Bài viết", description="Phân loại hệ thực thể (Bài viết hoặc Sản phẩm)")
    category_id: Optional[str] = Field(default=None, description="ID danh mục cụ thể từ Database (UUID)")
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
    content: str = Field(description="Tóm tắt ý chính (1-2 câu). TUYỆT ĐỐI KHÔNG chèn ảnh [IMAGE_X] ở bước này.")

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
    logs: List[str] = Field(default_factory=list, description="Live progress logs")

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
    logs: List[str] = Field(default_factory=list, description="Detailed progress logs for the UI")
    replacements: List[Dict[str, str]] = Field(default_factory=list, description="List of old vs new text to highlight in editor")

class SurgicalSnippetFix(BaseModel):
    model_config = ConfigDict(strict=True)
    id: int
    new_text: str

class AtomicFixResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    replacements: List[SurgicalSnippetFix]

# ── CNS V87.0: Surgeon Booster Schemas ──────────────────────────────────────
class ContentPatch(BaseModel):
    """Một thao tác phẫu thuật đơn lẻ: tìm search_string, thay bằng replacement_string."""
    model_config = ConfigDict(strict=True)
    search_string: str      # Đoạn text nguyên văn cần tìm trong content
    replacement_string: str # Đoạn text thay thế (cải tiến)
    rationale: str          # Giải thích ngắn gọn tại sao sửa

class SurgeonBoosterReport(BaseModel):
    """Kết quả phẫu thuật toàn bộ content từ Surgeon Agent."""
    model_config = ConfigDict(strict=True)
    patches: List[ContentPatch] = Field(default_factory=list)
    summary: str = ""
    logs: List[str] = Field(default_factory=list)

# ══════════════════════════════════════════════════════════════
# SCOUT & INTELLIGENCE SCHEMAS — V62.2 Elite
# ══════════════════════════════════════════════════════════════

class ScoutHeadline(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str = Field(description="Tiêu đề gợi ý bám sát thực tế")
    type: str = Field(description="Phân loại: ADS (Quảng cáo) | TOP_10 (SEO) | AI_AUGMENTED (Sáng tạo)")

class ScoutReport(BaseModel):
    model_config = ConfigDict(strict=True)
    topic: str
    headlines: List[ScoutHeadline]
    semantic_keywords: List[str]
    strategic_analysis: str = Field(description="Bản trình báo chiến lược AI chuyên sâu (Markdown)")
    ground_truth_summary: Optional[str] = Field(default=None, description="Tóm tắt bối cảnh trinh sát từ Google")
    logs: List[str] = Field(default_factory=list, description="Nhật ký trinh sát thời gian thực")

# ══════════════════════════════════════════════════════════════
# ANALYSIS & ENRICHMENT SCHEMAS — 2026 Edition
# ══════════════════════════════════════════════════════════════

class CopyrightAnnotation(BaseModel):
    model_config = ConfigDict(strict=True)
    text: str           # Exact text fragment from the article
    reason: str         # Why this is risky
    source_url: str     # Competitor URL
    severity: str       # "low" | "medium" | "high"
    type: Optional[str] = "external"

class PlagiarismResult(BaseModel):
    model_config = ConfigDict(strict=True)
    uniqueness_score: float = Field(description="Điểm số đánh giá mức độ độc bản, giá trị từ 0.0 (copy hoàn toàn) đến 1.0 (mới hoàn toàn)")
    risk_level: str
    flagged_sentences: List[str]
    annotations: List[CopyrightAnnotation]
    similar_sources: List[str]
    verdict: str
    logs: List[str] = Field(default_factory=list, description="Live progress logs")

class SeoAnnotation(BaseModel):
    model_config = ConfigDict(strict=True)
    type: str # "missing_h1", "keyword_missing", etc
    text: str
    message: str
    severity: str

class EnrichmentItem(BaseModel):
    model_config = ConfigDict(strict=False)
    type: str       # "stat" | "quote" | "table"
    location: str   # Where it was injected
    content: str    # The actual HTML injected

class EnrichAIPayload(BaseModel):
    model_config = ConfigDict(strict=False)
    new_content: str
    items: List[EnrichmentItem]
    stats_added: int
    quotes_added: int
    tables_added: int
    seo_boost_estimate: int

class EnrichResponse(EnrichAIPayload):
    annotations: List[SeoAnnotation] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list, description="Detailed progress logs for the UI")

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
    logs: List[str] = Field(default_factory=list, description="Detailed progress logs for the UI")

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
