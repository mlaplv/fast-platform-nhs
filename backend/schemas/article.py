from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator
from typing import Optional, List
from datetime import datetime
from backend.services.xohi.creative_studio.models.schemas import CategoryEnum
from backend.schemas.product import FaqItem


class ArticleMetadata(BaseModel):
    """GEO 2026: Article metadata — FAQs for Schema.org FAQPage."""
    model_config = ConfigDict(extra='allow', populate_by_name=True)
    faqs: List[FaqItem] = Field(default_factory=list, alias="faqs")
    how_to: Optional[dict] = Field(None, alias="how_to")
    # V2026: Single product linking for context-aware title generation
    related_product_id: Optional[str] = Field(None, alias="related_product_id")
    related_product_name: Optional[str] = Field(None, alias="related_product_name")
    related_product_image: Optional[str] = Field(None, alias="related_product_image")


class ArticleSeoMeta(BaseModel):
    """GEO 2026: Pre-computed SEO metadata for Article pages."""
    model_config = ConfigDict(strict=True)
    title: str
    description: str
    keywords: str
    canonical_url: str
    json_ld_string: str
    breadcrumb_ld_string: str = ""
    faq_ld_string: str = ""


class CreateArticleRequest(BaseModel):
    # CNS V95: strict=False for category to allow string coercion from query/form
    model_config = ConfigDict(strict=False, populate_by_name=True)
    title: str = Field(..., min_length=1, max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, max_length=200000)
    seo_title: Optional[str] = Field(None, max_length=500)
    seo_description: Optional[str] = Field(None, max_length=1000)
    seo_keywords: Optional[str] = Field(None, max_length=1000)
    seo_og_image: Optional[str] = Field(None, max_length=500)
    status: str = Field("DRAFT", pattern=r"^(DRAFT|PUBLISHED|ARCHIVED)$")
    category: str = Field(CategoryEnum.TIN_TUC.value)
    featured_image: Optional[str] = Field(None, alias="featured_image")
    metadata: Optional[ArticleMetadata] = None
    authorId: Optional[str] = None
    analysis_report: Optional[dict] = Field(None, alias="analysis_report")
    skip_embed_kg: Optional[bool] = Field(False, alias="skip_embed_kg")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: object) -> str:
        """Coerce CategoryEnum or arbitrary string to its .value safely."""
        if isinstance(v, CategoryEnum):
            return v.value
        if isinstance(v, str) and v.strip():
            return v.strip()
        return CategoryEnum.TIN_TUC.value


class UpdateArticleRequest(BaseModel):
    # CNS V95: strict=False for category to allow string coercion
    model_config = ConfigDict(strict=False, populate_by_name=True)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, max_length=200000)
    seo_title: Optional[str] = Field(None, max_length=500)
    seo_description: Optional[str] = Field(None, max_length=1000)
    seo_keywords: Optional[str] = Field(None, max_length=1000)
    seo_og_image: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|PUBLISHED|ARCHIVED)$")
    category: Optional[str] = Field(None)
    featured_image: Optional[str] = Field(None, alias="featured_image")
    metadata: Optional[ArticleMetadata] = None
    analysis_report: Optional[dict] = Field(None, alias="analysis_report")
    skip_embed_kg: Optional[bool] = Field(False, alias="skip_embed_kg")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: object) -> Optional[str]:
        """Coerce CategoryEnum or arbitrary string to its .value safely."""
        if v is None:
            return None
        if isinstance(v, CategoryEnum):
            return v.value
        if isinstance(v, str) and v.strip():
            return v.strip()
        return None


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: Optional[str] = None
    seoTitle: Optional[str] = Field(None, alias="seo_title")
    seoDescription: Optional[str] = Field(None, alias="seo_description")
    seoKeywords: Optional[str] = Field(None, alias="seo_keywords")
    seoOgImage: Optional[str] = Field(None, alias="seo_og_image")
    status: str
    category: str
    featuredImage: Optional[str] = Field(None, alias="featured_image")
    metadata: ArticleMetadata = Field(default_factory=ArticleMetadata, alias="article_metadata")
    seoMeta: Optional[ArticleSeoMeta] = Field(None, alias="seo_meta")
    analysis_report: Optional[dict] = Field(None, alias="analysis_report")
    views: int = 0
    author: str = Field("System", alias="author_name")
    authorId: Optional[str] = Field(None, alias="author_id")
    review_count: int = 0
    createdAt: datetime = Field(alias="created_at")
    updatedAt: Optional[datetime] = Field(None, alias="updated_at")
    upcoming_appointment: Optional[dict] = Field(None, alias="upcoming_appointment")

    @field_validator("author", mode="before")
    @classmethod
    def coerce_author(cls, v: object) -> str:
        """Handle None author from scalar projection when outer join fails."""
        if not v:
            return "System"
        return str(v)


    @field_validator("id", "authorId", mode="before")
    @classmethod
    def stringify_ids(cls, v: object) -> Optional[str]:
        return str(v) if v is not None else None

    @field_validator("category", mode="before")
    @classmethod
    def stringify_category(cls, v: object) -> str:
        """Handle CategoryEnum objects from ORM or raw strings from scalar projections."""
        if isinstance(v, CategoryEnum):
            return v.value
        if v is None:
            return CategoryEnum.TIN_TUC.value
        return str(v)

    @field_validator("metadata", mode="before")
    @classmethod
    def coerce_metadata(cls, v: object) -> object:
        """Safely handle None or empty dict from scalar projection."""
        if v is None:
            return {}
        return v

    @computed_field
    @property
    def display_status(self) -> str:
        return self.status.lower()

    @computed_field
    @property
    def reading_time(self) -> int:
        """Estimate reading time in minutes (200 words per minute)."""
        if not self.content:
            return 0
        words = len(self.content.split())
        return max(1, words // 200)


class ArticleListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[ArticleResponse]
    total: int
    next_cursor: Optional[str] = None
    has_more: Optional[bool] = None


class BulkPatchRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ids: List[str]
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|PUBLISHED|ARCHIVED)$")
    category: Optional[str] = Field(None, max_length=100)
