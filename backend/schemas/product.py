from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator, model_validator
from typing import Optional, List, Dict, Union, Any
# Elite 2026: Strict JSON Type (Rule R00)
JSONPrimitive = Union[str, int, float, bool, None]
JSONType = Union[JSONPrimitive, List[object], Dict[str, object]]
from datetime import datetime

class SeoMetaSchema(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str
    description: str
    keywords: str
    canonical_url: str
    json_ld_string: str


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
    fixed_price: float = Field(..., alias="fixed_price")
    label: str = Field(..., alias="label")
    scope: str = Field("global", alias="scope") # "global" | "variant_only"

class ProductMetadata(BaseModel):
    model_config = ConfigDict(extra='allow', populate_by_name=True)
    active_deals: List[PromotionDeal] = Field(default_factory=list, alias="active_deals")
    landing_type: Optional[str] = Field(None, alias="landing_type")
    scarcity_seconds: Optional[int] = Field(None, alias="scarcity_seconds")
    show_reviews: Optional[bool] = Field(None, alias="show_reviews")
    video_url: Optional[str] = Field(None, alias="video_url")

    # R00 Compliance: Externalized UI Labels
    sync_loading_text: Optional[str] = Field(None, alias="sync_loading_text")
    seo_site_name: Optional[str] = Field(None, alias="seo_site_name")

    # Section: Reviews
    reviews_headline: Optional[str] = Field(None, alias="reviews_headline")
    reviews_trust_score: Optional[str] = Field(None, alias="reviews_trust_score")
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

class ProductVariantSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)
    id: Optional[str] = None
    tierIndex: List[int] = Field(default_factory=list, alias="tier_index")
    sku: Optional[str] = None
    price: float
    discountPrice: Optional[float] = Field(None, alias="discount_price")
    stock: int

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
    stock: int = Field(0, ge=0)
    status: str = Field("DRAFT", pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")
    shortDescription: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = Field(None, max_length=100000)
    categoryId: Optional[str] = None
    type: str = Field("RETAIL", pattern=r"^(RETAIL|RENTAL|SERVICE)$")
    
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
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")
    shortDescription: Optional[str] = Field(None, max_length=1000)
    description: Optional[str] = Field(None, max_length=100000)
    categoryId: Optional[str] = None
    
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
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)

    id: str
    name: str
    sku: Optional[str] = ""
    price: float
    discountPrice: Optional[float] = Field(None, alias="discount_price")
    stock: int
    status: str
    category: Optional[str] = Field("", alias="category_name")
    categoryId: Optional[str] = Field(None, alias="category_id")
    shortDescription: Optional[str] = Field(None, alias="short_description")
    description: Optional[str] = None
    type: str = "RETAIL"
    
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
    orderCountText: str = Field("2,140+ LƯỢT MUA", alias="order_count_text")

    createdAt: datetime = Field(alias="created_at")

    @field_validator("id", "categoryId", mode="before")
    @classmethod
    def stringify_ids(cls, v):
        return str(v) if v is not None else None

    @field_validator("images", "mobileImages", mode="before")
    @classmethod
    def validate_images(cls, v):
        if v is None: return []
        if isinstance(v, list):
            return [str(x) for x in v if x is not None]
        return v

    @field_validator("attributes", mode="before")
    @classmethod
    def validate_attributes(cls, v):
        return v if v is not None else {}

    @field_validator("metadata", mode="before")
    @classmethod
    def validate_metadata(cls, v):
        return v if v is not None else {}

    @field_validator("tierVariations", "variants", mode="before")
    @classmethod
    def validate_matrix_fields(cls, v):
        if v is None: return []
        if isinstance(v, list):
            return [x for x in v if x is not None]
        return v

    @field_validator("sku", mode="before")
    @classmethod
    def validate_sku(cls, v):
        return str(v) if v is not None else ""

    @computed_field
    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0

    @computed_field
    @property
    def display_status(self) -> str:
        return self.status.lower()


class ProductListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[ProductResponse]
    total: int
