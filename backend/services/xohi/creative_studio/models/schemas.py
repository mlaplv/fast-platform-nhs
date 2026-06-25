from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
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

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_text_block
        return validate_vietnamese_text_block(v)

class ArticleOutline(BaseModel):
    model_config = ConfigDict(strict=False)  # R105: Guarded validation (lenient for LLM stability)
    sections: List[OutlineSection] = Field(description="Danh sách các H2, H3 và mô tả nội dung kèm vị trí chèn ảnh [IMAGE_X]")

class VisualSearchPlan(BaseModel):
    model_config = ConfigDict(strict=True)
    queries: List[str] = Field(description="List of 3-5 high-quality Google Image search queries (English preferred for professional stock quality)")

class AiAnnotation(BaseModel):
    model_config = ConfigDict(strict=True)
    type: str      # "search_intent" | "eeat_missing" | "geo_stats" | "ai_overview" | "snippet_ready" | "entity_gap" | "geo_fluff" | "citation_weak" | "geo_quotes" | "seo_gap" | "copyright_risk"
    text: str      # Exact substring from the article to highlight
    message: str   # Vietnamese tip shown in tooltip
    severity: str  # "high" | "warning" | "info"

class AiReadyReport(BaseModel):
    model_config = ConfigDict(strict=True)
    geo_score: int
    summary: str
    ai_annotations: List[AiAnnotation] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list, description="Live progress logs")

    @field_validator('summary')
    @classmethod
    def validate_summary(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_text_block
        return validate_vietnamese_text_block(v)

class AutoFixResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    old_text: str
    new_text: str

    @field_validator('new_text')
    @classmethod
    def validate_new_text(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_sentence, sanitize_sentence_linebreaks
        v = sanitize_sentence_linebreaks(v)
        return validate_vietnamese_sentence(v, mode="standard")

class BulkFixRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    category: str      # "copyright" | "seo" | "ai"
    annotations: List[Dict[str, object]]

class BulkFixResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    new_content: str
    logs: List[str] = Field(default_factory=list, description="Detailed progress logs for the UI")
    replacements: List[Dict[str, str]] = Field(default_factory=list, description="List of old vs new text to highlight in editor")

    @field_validator('new_content')
    @classmethod
    def validate_new_content(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_text_block
        import logging
        logger = logging.getLogger("api-gateway")
        try:
            return validate_vietnamese_text_block(v)
        except Exception as e:
            logger.warning(f"⚠️ [BulkFixResponse] new_content failed strict validation, falling back to raw output: {e}")
            return v

class SnippetRefinement(BaseModel):
    model_config = ConfigDict(strict=True)
    id: int
    new_text: str

    @field_validator('new_text')
    @classmethod
    def validate_new_text(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_sentence, sanitize_sentence_linebreaks
        import logging
        logger = logging.getLogger("api-gateway")
        v = sanitize_sentence_linebreaks(v)
        try:
            return validate_vietnamese_sentence(v, mode="standard")
        except Exception as e:
            logger.warning(f"⚠️ [SnippetRefinement] new_text validation warning: {e}")
            return v

class AtomicFixResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    replacements: List[SnippetRefinement]

# ── CNS V87.0: Neural Booster Schemas ──────────────────────────────────────
class ContentPatch(BaseModel):
    """Một thao tác tinh chỉnh đơn lẻ: tìm search_string, thay bằng replacement_string."""
    model_config = ConfigDict(strict=True)
    search_string: str      # Đoạn text nguyên văn cần tìm trong content
    replacement_string: str # Đoạn text thay thế (cải tiến)
    rationale: str          # Giải thích ngắn gọn tại sao sửa

    @field_validator('replacement_string')
    @classmethod
    def validate_replacement_string(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_sentence, sanitize_sentence_linebreaks
        import logging
        logger = logging.getLogger("api-gateway")
        v = sanitize_sentence_linebreaks(v)
        try:
            return validate_vietnamese_sentence(v, mode="standard")
        except Exception as e:
            logger.warning(f"⚠️ [ContentPatch] replacement_string validation warning: {e}")
            return v


# ── CNS V93.0: Structured Clinical Evidence ─────────────────────────────────
class KeyStat(BaseModel):
    """
    Một chỉ số/số liệu cụ thể trích từ nghiên cứu.
    Dùng để inject <blockquote class='xohi-stat'> và build data tables.
    """
    model_config = ConfigDict(strict=False)
    label: str       # Tên chỉ số (VD: "Hiệu quả giảm nếp nhăn")
    value: str       # Giá trị đo (VD: "43%", "2.1 mg/dL")
    unit: str = ""   # Đơn vị (VD: "%", "mg", "mmHg") — rỗng nếu đã kèm trong value
    note: str = ""   # Điều kiện/ghi chú (VD: "RCT, n=120, 8 tuần")


class ClinicalDataTable(BaseModel):
    """
    CNS V93.0: Bảng số liệu lâm sàng có cấu trúc — sẵn sàng render HTML.
    Tối ưu cho SGE, AI Overview và semantic indexing.
    """
    model_config = ConfigDict(strict=False)
    table_title: str             # Tiêu đề bảng (tiếng Việt)
    source_citation: str         # (Tên nguồn, Năm) — format cite
    source_url: str = ""         # URL gốc để verify (nếu có)
    headers: List[str]           # Danh sách tên cột
    rows: List[List[str]]        # Data rows (ma trận 2D)
    table_type: str = "efficacy" # "comparison" | "efficacy" | "safety" | "ingredient"
    caption_vi: str = ""         # Mô tả bảng tiếng Việt (cho <figcaption>)


class ClinicalSource(BaseModel):
    """
    CNS V93.0: Bằng chứng lâm sàng đã được trinh sát, dịch thuần Việt & extract số liệu.
    Đảm bảo minh bạch nguồn gốc & khả năng verify độc lập.
    """
    model_config = ConfigDict(strict=False)
    title_vi: str                    # Tiêu đề bài nghiên cứu dịch sang tiếng Việt
    title_original: str              # Tiêu đề gốc (JP/EN) để verify
    source_domain: str               # Tên nguồn: J-STAGE / PubMed / WHO / PMDA / JSCC...
    source_url: str                  # URL gốc để đọc thêm
    year: str                        # Năm công bố hoặc "N/A"
    snippet_vi: str                  # Trích đoạn đã dịch sang tiếng Việt chuẩn
    relevance: str                   # Giải thích ngắn tại sao nguồn này liên quan đến topic
    key_stats: List[KeyStat] = Field(  # CNS V93.0: Số liệu cụ thể trích được
        default_factory=list,
        description="Tối đa 3 chỉ số/số liệu thực tế trích từ nghiên cứu này"
    )


class NeuralBoosterReport(BaseModel):
    """CNS V93.0: Kết quả tinh chỉnh toàn bộ content từ Neural Booster Agent."""
    model_config = ConfigDict(strict=True)
    patches: List[ContentPatch] = Field(default_factory=list)
    summary: str = ""
    logs: List[str] = Field(default_factory=list)
    clinical_sources: List[ClinicalSource] = Field(
        default_factory=list,
        description="Danh sách nguồn lâm sàng uy tín đã trinh sát & dịch Việt"
    )
    data_tables: List[ClinicalDataTable] = Field(  # CNS V93.0: Bảng số liệu có cấu trúc
        default_factory=list,
        description="Bảng số liệu lâm sàng tổng hợp từ nhiều nguồn — sẵn sàng inject HTML"
    )

    @field_validator('summary')
    @classmethod
    def validate_summary(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_text_block
        return validate_vietnamese_text_block(v)

# ══════════════════════════════════════════════════════════════
# SCOUT & INTELLIGENCE SCHEMAS — V62.2 Elite
# ══════════════════════════════════════════════════════════════

class ScoutHeadline(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str = Field(description="Tiêu đề gợi ý bám sát thực tế")
    type: str = Field(description="Phân loại: ADS (Quảng cáo) | TOP_10 (SEO) | AI_AUGMENTED (Sáng tạo)")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_sentence
        return validate_vietnamese_sentence(v, mode="light")

class ScoutReport(BaseModel):
    model_config = ConfigDict(strict=True)
    topic: str
    headlines: List[ScoutHeadline]
    semantic_keywords: List[str]
    strategic_analysis: str = Field(description="Bản trình báo chiến lược AI chuyên sâu (Markdown)")
    ground_truth_summary: Optional[str] = Field(default=None, description="Tóm tắt bối cảnh trinh sát từ Google")
    logs: List[str] = Field(default_factory=list, description="Nhật ký trinh sát thời gian thực")

    @field_validator('strategic_analysis')
    @classmethod
    def validate_strategic_analysis(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_text_block
        return validate_vietnamese_text_block(v)

    @field_validator('ground_truth_summary')
    @classmethod
    def validate_ground_truth_summary(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        from backend.utils.text import validate_vietnamese_text_block
        return validate_vietnamese_text_block(v)

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
    verdict_gap: str = Field(default="", description="Nội dung chi tiết phần: 1. LUẬN ĐIỂM PHẢN BIỆN (Markdown). KHÔNG kèm tiêu đề.")
    verdict_evidence: str = Field(default="", description="Nội dung chi tiết phần: 2. HỒ SƠ CHỨNG CỨ VÀ NGHIÊN CỨU (Markdown). KHÔNG kèm tiêu đề.")
    verdict_strategy: str = Field(default="", description="Nội dung chi tiết phần: 3. CHIẾN LƯỢC TÁI CẤU TRÚC (Markdown). Trình bày đầy đủ 3 bước. KHÔNG kèm tiêu đề.")
    verdict: str = Field(default="", description="Trường này hệ thống tự tổng hợp, hãy bỏ trống.")
    logs: List[str] = Field(default_factory=list, description="Live progress logs")

    @field_validator('verdict_gap', 'verdict_evidence', 'verdict_strategy')
    @classmethod
    def validate_verdicts(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_text_block
        return validate_vietnamese_text_block(v)

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

    @field_validator('summary')
    @classmethod
    def validate_summary(cls, v: str) -> str:
        from backend.utils.text import validate_vietnamese_text_block
        return validate_vietnamese_text_block(v)

    @field_validator('quick_wins')
    @classmethod
    def validate_quick_wins(cls, v: List[str]) -> List[str]:
        from backend.utils.text import validate_vietnamese_sentence
        for item in v:
            validate_vietnamese_sentence(item)
        return v

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
