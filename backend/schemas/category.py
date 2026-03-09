from pydantic import BaseModel, Field
from typing import Optional


class CreateCategoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=200, pattern=r"^[a-z0-9-]+$")
    parentId: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=200, pattern=r"^[a-z0-9-]+$")
