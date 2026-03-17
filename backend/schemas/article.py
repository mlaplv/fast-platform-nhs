from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator
from typing import Optional, List
from datetime import datetime


class CreateArticleRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str = Field(..., min_length=1, max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, max_length=50000)
    seo_title: Optional[str] = Field(None, max_length=500)
    seo_description: Optional[str] = Field(None, max_length=1000)
    status: str = Field("DRAFT", pattern=r"^(DRAFT|PUBLISHED|ARCHIVED)$")
    category: str = Field("Tin tức", max_length=100)
    authorId: Optional[str] = None


class UpdateArticleRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, max_length=50000)
    seo_title: Optional[str] = Field(None, max_length=500)
    seo_description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|PUBLISHED|ARCHIVED)$")
    category: Optional[str] = Field(None, max_length=100)


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)

    id: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: Optional[str] = None
    seoTitle: Optional[str] = Field(None, alias="seo_title")
    seoDescription: Optional[str] = Field(None, alias="seo_description")
    status: str
    category: str
    views: int = 0
    author: str = Field("System", alias="author_name")
    authorId: Optional[str] = Field(None, alias="author_id")
    createdAt: datetime = Field(alias="created_at")

    @field_validator("id", "authorId", mode="before")
    @classmethod
    def stringify_ids(cls, v):
        return str(v) if v is not None else None

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
