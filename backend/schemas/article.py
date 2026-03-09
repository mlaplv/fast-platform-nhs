from pydantic import BaseModel, Field
from typing import Optional


class CreateArticleRequest(BaseModel):
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
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    slug: Optional[str] = Field(None, max_length=500)
    excerpt: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, max_length=50000)
    seo_title: Optional[str] = Field(None, max_length=500)
    seo_description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|PUBLISHED|ARCHIVED)$")
    category: Optional[str] = Field(None, max_length=100)


class BulkIdsRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1, max_length=100)
