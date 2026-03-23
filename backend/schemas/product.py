from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator
from typing import Optional, List, Dict, Union
from datetime import datetime


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, strict=True)
    name: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=50)
    price: float = Field(0, ge=0)
    stock: int = Field(0, ge=0)
    status: str = Field("DRAFT", pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")
    description: Optional[str] = Field(None, max_length=5000)
    categoryId: Optional[str] = None
    type: str = Field("RETAIL", pattern=r"^(RETAIL|RENTAL|SERVICE)$")
    
    # Professional Fashion Upgrade
    slug: str = Field(..., min_length=1, max_length=200)
    seoTitle: Optional[str] = Field(None, max_length=200, alias="seo_title")
    seoDescription: Optional[str] = Field(None, max_length=500, alias="seo_description")
    seoKeywords: Optional[str] = Field(None, max_length=500, alias="seo_keywords")
    images: List[str] = Field(default_factory=list)
    attributes: Dict[str, Union[str, int, float, bool, None]] = Field(default_factory=dict)


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, strict=True)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=50)
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")
    description: Optional[str] = Field(None, max_length=5000)
    categoryId: Optional[str] = None
    
    # Professional Fashion Upgrade
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    seoTitle: Optional[str] = Field(None, max_length=200, alias="seo_title")
    seoDescription: Optional[str] = Field(None, max_length=500, alias="seo_description")
    seoKeywords: Optional[str] = Field(None, max_length=500, alias="seo_keywords")
    images: Optional[List[str]] = None
    attributes: Optional[Dict[str, Union[str, int, float, bool, None]]] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)

    id: str
    name: str
    sku: str = ""
    price: float
    stock: int
    status: str
    category: str = Field("", alias="category_name")
    categoryId: Optional[str] = Field(None, alias="category_id")
    description: Optional[str] = None
    type: str = "RETAIL"
    
    # Professional Fashion Upgrade
    slug: str
    seoTitle: Optional[str] = Field(None, alias="seo_title")
    seoDescription: Optional[str] = Field(None, alias="seo_description")
    seoKeywords: Optional[str] = Field(None, alias="seo_keywords")
    images: List[str] = Field(default_factory=list)
    attributes: Dict[str, Union[str, int, float, bool, None]] = Field(default_factory=dict)
    createdAt: datetime = Field(alias="created_at")

    @field_validator("id", "categoryId", mode="before")
    @classmethod
    def stringify_ids(cls, v):
        return str(v) if v is not None else None

    @field_validator("images", mode="before")
    @classmethod
    def validate_images(cls, v):
        return v if v is not None else []

    @field_validator("attributes", mode="before")
    @classmethod
    def validate_attributes(cls, v):
        return v if v is not None else {}

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
