from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from typing import Optional, List
from datetime import datetime


class CreateCategoryRequest(BaseModel):
    model_config = ConfigDict(strict=True, populate_by_name=True)
    name: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=200, pattern=r"^[a-z0-9-]+$")
    parentId: Optional[str] = None

    # Professional Fashion Upgrade
    description: Optional[str] = Field(None, max_length=5000)
    seoTitle: Optional[str] = Field(None, max_length=200, alias="seo_title")
    seoDescription: Optional[str] = Field(None, max_length=500, alias="seo_description")
    image: Optional[str] = None
    icon: Optional[str] = None
    position: int = 0
    showOnMobile: bool = Field(True, alias="show_on_mobile")
    showOnDesktop: bool = Field(True, alias="show_on_desktop")


class UpdateCategoryRequest(BaseModel):
    model_config = ConfigDict(strict=True, populate_by_name=True)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=200, pattern=r"^[a-z0-9-]+$")
    parentId: Optional[str] = None

    # Professional Fashion Upgrade
    description: Optional[str] = Field(None, max_length=5000)
    seoTitle: Optional[str] = Field(None, max_length=200, alias="seo_title")
    seoDescription: Optional[str] = Field(None, max_length=500, alias="seo_description")
    image: Optional[str] = None
    icon: Optional[str] = None
    position: Optional[int] = None
    showOnMobile: Optional[bool] = Field(None, alias="show_on_mobile")
    showOnDesktop: Optional[bool] = Field(None, alias="show_on_desktop")


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    slug: str
    parentId: Optional[str] = Field(None, alias="parent_id")
    productCount: int = Field(0, alias="product_count")
    
    # Professional Fashion Upgrade
    description: Optional[str] = None
    seoTitle: Optional[str] = Field(None, alias="seo_title")
    seoDescription: Optional[str] = Field(None, alias="seo_description")
    image: Optional[str] = None
    icon: Optional[str] = None
    position: int = 0
    showOnMobile: bool = Field(True, alias="show_on_mobile")
    showOnDesktop: bool = Field(True, alias="show_on_desktop")
    
    children: List["CategoryResponse"] = Field(default_factory=list)
    createdAt: datetime = Field(alias="created_at")

    @field_validator("id", "parentId", mode="before")
    @classmethod
    def stringify_ids(cls, v):
        return str(v) if v is not None else None

    @computed_field
    @property
    def has_children(self) -> bool:
        return len(self.children) > 0


class CategoryListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    data: List[CategoryResponse]
    total: int


CategoryResponse.model_rebuild()
