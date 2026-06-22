import os
from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator, model_validator
from typing import Optional, List, Dict, Union
# Elite 2026: Strict JSON Type (Rule R00)
JSONPrimitive = Union[str, int, float, bool, None]
JSONType = Union[JSONPrimitive, List[object], Dict[str, object]]
from datetime import datetime

class FaqItem(BaseModel):
    """Elite V2.2: Structured FAQ for Product Detail + Schema.org FAQPage."""
    model_config = ConfigDict(strict=True)
    question: str
    answer: str

class FeaturedIngredientItem(BaseModel):
    """Elite V2.2: Structured Featured Ingredient for Product Detail."""
    model_config = ConfigDict(strict=True, populate_by_name=True)
    name: str
    benefit: str
    icon: Optional[str] = ""

class SeoMetaSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str
    description: str
    keywords: str
    canonical_url: str
    json_ld_string: str
    breadcrumb_ld_string: str = ""
    faq_ld_string: str = ""


class TierVariation(BaseModel):
    name: str
    options: List[str]
    images: Optional[List[str]] = None
    mobile_images: Optional[List[str]] = None

    @field_validator("images", "mobile_images", mode="before")
    @classmethod
    def filter_null_images(cls, v: object) -> List[str]:
        if v is None: return []
        if isinstance(v, list):
            return [str(x) for x in v if x is not None]
        return v

class PromotionDeal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    buy_qty: int = Field(..., alias="buy_qty")
    get_qty: int = Field(..., alias="get_qty")
    fixed_price: Optional[float] = Field(0.0, alias="fixed_price")
    label: str = Field(..., alias="label")
    scope: str = Field("global", alias="scope")

class ProductMetadata(BaseModel):
    model_config = ConfigDict(extra='allow', populate_by_name=True)
    active_deals: List[PromotionDeal] = Field(default_factory=list, alias="active_deals")
    landing_type: Optional[str] = Field(None, alias="landing_type")
    scarcity_seconds: Optional[int] = Field(None, alias="scarcity_seconds")
    show_reviews: Optional[bool] = Field(None, alias="show_reviews")
    video_url: Optional[str] = Field(None, alias="video_url")
    video_start_time: Optional[float] = Field(None, alias="video_start_time")
    video_end_time: Optional[float] = Field(None, alias="video_end_time")
    mobile_video_url: Optional[str] = Field(None, alias="mobile_video_url")
    mobile_video_start_time: Optional[float] = Field(None, alias="mobile_video_start_time")
    mobile_video_end_time: Optional[float] = Field(None, alias="mobile_video_end_time")

    # Elite 2026: AI Customer Sentiment Summary
    customer_sentiment_summary: Optional[str] = Field(None, alias="customer_sentiment_summary")
    positive_notes: List[str] = Field(default_factory=list, alias="positive_notes")
    negative_notes: List[str] = Field(default_factory=list, alias="negative_notes")

    # Elite V2.2: Viral Infrastructure (Config chính thống)
    share_promotion: Optional[Dict[str, JSONType]] = Field(default_factory=dict, alias="share_promotion")
    viral_suite: Optional[Dict[str, JSONType]] = Field(default_factory=dict, alias="viral_suite")
    share_count: int = Field(0, alias="share_count")
    likes: int = Field(0, alias="likes")

    # Elite V2.2: Product FAQs (Tùy biến từ Admin → hiện trên Product Detail + Schema JSON-LD)
    faqs: List[FaqItem] = Field(default_factory=list, alias="faqs")
    faqs_total: Optional[int] = Field(None, alias="faqs_total")

    # Elite V2.2: Featured Ingredients
    featured_ingredients: List[FeaturedIngredientItem] = Field(default_factory=list, alias="featured_ingredients")

    # R00 Compliance: Externalized UI Labels
    sync_loading_text: Optional[str] = Field(None, alias="sync_loading_text")
    seo_site_name: Optional[str] = Field(None, alias="seo_site_name")

    # Section: Hero Spotlight
    hero_headline: Optional[str] = Field(None, alias="hero_headline")
    hero_cta_text: Optional[str] = Field(None, alias="hero_cta_text")
    hero_product_name_fallback: Optional[str] = Field(None, alias="hero_product_name_fallback")
    hero_metrics: List[Dict[str, JSONType]] = Field(default_factory=list, alias="hero_metrics")

    # Section: Reviews
    reviews_headline: Optional[str] = Field(None, alias="reviews_headline")
    reviews_subheadline: Optional[str] = Field(None, alias="reviews_subheadline")
    reviews_trust_score: Optional[float] = Field(None, alias="reviews_trust_score")
    review_count: Optional[int] = Field(None, alias="review_count")
    reviews_count_text: Optional[str] = Field(None, alias="reviews_count_text")
    reviews: List[Dict[str, JSONType]] = Field(default_factory=list, alias="reviews")

    # Section: Diagnostics
    diagnostics_headline: Optional[str] = Field(None, alias="diagnostics_headline")
    diagnostics_subheadline: Optional[str] = Field(None, alias="diagnostics_subheadline")
    diagnostics_disclaimer: Optional[str] = Field(None, alias="diagnostics_disclaimer")
    quiz_questions: List[Dict[str, JSONType]] = Field(default_factory=list, alias="quiz_questions")

    # Section: Science
    science_headline: Optional[str] = Field(None, alias="science_headline")
    science_subheadline: Optional[str] = Field(None, alias="science_subheadline")
    science_image: Optional[str] = Field(None, alias="science_image")
    science_card1_title: Optional[str] = Field(None, alias="science_card1_title")
    science_card1_desc: Optional[str] = Field(None, alias="science_card1_desc")
    science_card2_title: Optional[str] = Field(None, alias="science_card2_title")
    science_card2_desc: Optional[str] = Field(None, alias="science_card2_desc")

    # Section: Offer Grid
    offer_headline: Optional[str] = Field(None, alias="offer_headline")
    offer_subheadline: Optional[str] = Field(None, alias="offer_subheadline")
    offer_timer_prefix: Optional[str] = Field(None, alias="offer_timer_prefix")
    offer_trust_verified_by: Optional[str] = Field(None, alias="offer_trust_verified_by")
    offer_pharmacy_name: Optional[str] = Field(None, alias="offer_pharmacy_name")
    offer_pharmacy_address: Optional[str] = Field(None, alias="offer_pharmacy_address")
    offer_pharmacy_phone: Optional[str] = Field(None, alias="offer_pharmacy_phone")
    offer_pharmacy_zalo: Optional[str] = Field(None, alias="offer_pharmacy_zalo")

    # Section: Checkout
    checkout_headline: Optional[str] = Field(None, alias="checkout_headline")
    checkout_subheadline: Optional[str] = Field(None, alias="checkout_subheadline")
    checkout_cta_text: Optional[str] = Field(None, alias="checkout_cta_text")
    checkout_variant_title: Optional[str] = Field(None, alias="checkout_variant_title")

class VariantAttributes(BaseModel):
    model_config = ConfigDict(extra='allow', populate_by_name=True)
    combo_qty: Optional[int] = Field(None, alias="combo_qty")
    gifts: List[Dict[str, JSONType]] = Field(default_factory=list, alias="gifts")

class ProductVariantSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: Optional[str] = None
    tierIndex: List[int] = Field(default_factory=list, alias="tier_index")
    sku: Optional[str] = None
    price: float
    discountPrice: Optional[float] = Field(None, alias="discount_price")
    discountPercent: Optional[float] = Field(None, alias="discount_percent")
    stock: int
    attributes: Optional[VariantAttributes] = Field(None)
    is_default: bool = False

    @field_validator("tierIndex", mode="before")
    @classmethod
    def validate_tier_index(cls, v: object) -> List[int]:
        if v is None: return []
        if isinstance(v, list):
            return [int(x) for x in v if x is not None]
        return v

    @model_validator(mode="after")
    def validate_variant_price(self) -> "ProductVariantSchema":
        dp = self.discountPrice
        p = self.price
        if dp is not None and p is not None and dp >= p:
            raise ValueError("Giá khuyến mãi phải nhỏ hơn giá bán")
        return self

class CreateProductRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, strict=True)
    name: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=50)
    price: float = Field(0, ge=0)
    discountPrice: Optional[float] = Field(None, ge=0, alias="discount_price")
    discountPercent: Optional[float] = Field(None, ge=0, alias="discount_percent")
    stock: int = Field(0, ge=0)
    status: str = Field("DRAFT", pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")
    shortDescription: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = Field(None, max_length=100000)
    categoryId: Optional[str] = None
    type: str = Field("RETAIL", pattern=r"^(RETAIL|RENTAL|SERVICE)$")
    isAiFeatured: bool = Field(False, alias="is_ai_featured")
    ctvRateOverride: Optional[float] = Field(None, ge=0, le=1.0, alias="ctv_rate_override")
    analysis_report: Optional[Dict[str, object]] = Field(None, alias="analysis_report")
    generate_knowledge_graph: bool = Field(False, alias="generate_knowledge_graph")
    
    # Professional Fashion Upgrade
    slug: str = Field(..., min_length=1, max_length=200)
    seoTitle: Optional[str] = Field(None, max_length=200, alias="seo_title")
    seoDescription: Optional[str] = Field(None, max_length=2000, alias="seo_description")
    seoKeywords: Optional[str] = Field(None, max_length=2000, alias="seo_keywords")
    images: List[str] = Field(default_factory=list)
    mobileImages: List[str] = Field(default_factory=list, alias="mobile_images")
    attributes: Dict[str, Union[str, int, float, bool, None]] = Field(default_factory=dict)
    metadata: ProductMetadata = Field(default_factory=ProductMetadata)

    # R102 Variants Matrix
    tierVariations: List[TierVariation] = Field(default_factory=list, alias="tier_variations")
    variants: List[ProductVariantSchema] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_base_price(self) -> "CreateProductRequest":
        dp = self.discountPrice
        p = self.price
        if dp is not None and p is not None and dp >= p:
            raise ValueError("Giá khuyến mãi phải nhỏ hơn giá bán")
        return self

class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, strict=True)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=50)
    price: Optional[float] = Field(None, ge=0)
    discountPrice: Optional[float] = Field(None, ge=0, alias="discount_price")
    discountPercent: Optional[float] = Field(None, ge=0, alias="discount_percent")
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")
    shortDescription: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = Field(None, max_length=100000)
    categoryId: Optional[str] = None
    isAiFeatured: Optional[bool] = Field(None, alias="is_ai_featured")
    ctvRateOverride: Optional[float] = Field(None, ge=0, le=1.0, alias="ctv_rate_override")
    analysis_report: Optional[Dict[str, object]] = Field(None, alias="analysis_report")
    generate_knowledge_graph: Optional[bool] = Field(False, alias="generate_knowledge_graph")
    
    # Professional Fashion Upgrade
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    seoTitle: Optional[str] = Field(None, max_length=200, alias="seo_title")
    seoDescription: Optional[str] = Field(None, max_length=2000, alias="seo_description")
    seoKeywords: Optional[str] = Field(None, max_length=2000, alias="seo_keywords")
    images: Optional[List[str]] = None
    mobileImages: Optional[List[str]] = Field(None, alias="mobile_images")
    attributes: Optional[Dict[str, Union[str, int, float, bool, None]]] = None
    metadata: Optional[ProductMetadata] = None

    # R102 Variants Matrix
    tierVariations: Optional[List[TierVariation]] = Field(None, alias="tier_variations")
    variants: Optional[List[ProductVariantSchema]] = None

    @model_validator(mode="after")
    def validate_update_price(self) -> "UpdateProductRequest":
        dp = self.discountPrice
        p = self.price
        if dp is not None and p is not None and dp >= p:
            raise ValueError("Giá khuyến mãi phải nhỏ hơn giá bán")
        return self

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    sku: Optional[str] = ""
    price: float
    discountPrice: Optional[float] = Field(None, alias="discount_price")
    discountPercent: Optional[float] = Field(None, alias="discount_percent")
    stock: int
    status: str
    category: Optional[str] = Field("", alias="category_name")
    categorySlug: Optional[str] = Field("", alias="category_slug")
    categoryId: Optional[str] = Field(None, alias="category_id")
    shortDescription: Optional[str] = Field(None, alias="short_description")
    description: Optional[str] = None
    type: str = "RETAIL"
    isAiFeatured: bool = Field(False, alias="is_ai_featured")
    ctvRateOverride: Optional[float] = Field(None, alias="ctv_rate_override")
    analysis_report: Optional[Dict[str, object]] = Field(None, alias="analysis_report")
    
    # Professional Fashion Upgrade
    slug: str
    seoTitle: Optional[str] = Field(None, alias="seo_title")
    seoDescription: Optional[str] = Field(None, alias="seo_description")
    seoKeywords: Optional[str] = Field(None, alias="seo_keywords")
    images: List[str] = Field(default_factory=list)
    mobileImages: List[str] = Field(default_factory=list, alias="mobile_images")
    attributes: Dict[str, Union[str, int, float, bool, None]] = Field(default_factory=dict)
    metadata: ProductMetadata = Field(default_factory=ProductMetadata)
    seoMeta: Optional[SeoMetaSchema] = Field(None, alias="seo_meta")

    # R102 Variants Matrix
    tierVariations: List[TierVariation] = Field(default_factory=list, alias="tier_variations")
    variants: List[ProductVariantSchema] = Field(default_factory=list)
    
    orderCount: int = Field(0, alias="order_count")
    orderCountText: Optional[str] = Field(None, alias="order_count_text")
    review_count: int = 0

    # Market Price Intel (V2026)
    marketData: Optional[Dict[str, object]] = Field(None, alias="market_data")
    lastMarketSync: Optional[datetime] = Field(None, alias="last_market_sync")

    createdAt: datetime = Field(alias="created_at")

    @model_validator(mode="before")
    @classmethod
    def convert_bps_fields(cls, data: object) -> object:
        """BPS Migration Fix: convert ctv_rate_override_bps (int) → ctv_rate_override (float)
        sau khi column rename trong v606_financial_hardening_bigint_uuidv7."""
        if isinstance(data, dict):
            bps_val = data.pop("ctv_rate_override_bps", None)
            if bps_val is not None and "ctv_rate_override" not in data:
                data["ctv_rate_override"] = bps_val / 10000.0
        return data

    @field_validator("id", "categoryId", mode="before")
    @classmethod
    def stringify_ids(cls, v: object) -> Optional[str]:
        return str(v) if v is not None else None

    @field_validator("images", "mobileImages", mode="before")
    @classmethod
    def validate_images(cls, v: object) -> List[str]:
        if v is None: return []
        if isinstance(v, list):
            return [str(x) for x in v if x is not None]
        return v

    @field_validator("attributes", mode="before")
    @classmethod
    def validate_attributes(cls, v: object) -> Dict[str, Union[str, int, float, bool, None]]:
        return v if isinstance(v, dict) else {}

    @field_validator("metadata", mode="before")
    @classmethod
    def validate_metadata(cls, v: object) -> Dict[str, object]:
        return v if isinstance(v, dict) else {}

    @field_validator("tierVariations", "variants", mode="before")
    @classmethod
    def validate_matrix_fields(cls, v: object) -> List[object]:
        if v is None: return []
        if isinstance(v, list):
            return [x for x in v if x is not None]
        return v

    @field_validator("sku", mode="before")
    @classmethod
    def validate_sku(cls, v: object) -> str:
        return str(v) if v is not None else ""

    @model_validator(mode="after")
    def generate_order_count_text(self) -> "ProductResponse":
        # Elite V2.2: Zero-Hardcode dynamic text generation
        # Marketing Offset is now handled in Service Layer for consistency.
        
        total_count = self.orderCount
        dummy = "2,140+ LƯỢT MUA"
        
        if not self.orderCountText or self.orderCountText == dummy:
            if total_count > 0:
                if total_count >= 1000:
                    self.orderCountText = f"{total_count:,}+ LƯỢT MUA"
                else:
                    self.orderCountText = f"ĐÃ BÁN {total_count}"
            else:
                self.orderCountText = ""
        return self

    @computed_field
    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0

    @computed_field
    @property
    def display_status(self) -> str:
        return self.status.lower()


class SearchFacets(BaseModel):
    """Elite V2.2: Dynamic filter options derived from actual search results."""
    model_config = ConfigDict(strict=True)
    brands: List[str] = Field(default_factory=list)
    origins: List[str] = Field(default_factory=list)
    price_min: float = Field(0.0)
    price_max: float = Field(0.0)


class ProductListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[ProductResponse]
    total: int
    facets: Optional[SearchFacets] = None
    next_cursor: Optional[str] = None
    has_more: Optional[bool] = None


class BulkUpdateProductRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, strict=True)
    ids: List[str]
    data: UpdateProductRequest
