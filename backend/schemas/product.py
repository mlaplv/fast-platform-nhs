from pydantic import BaseModel, Field
from typing import Optional


class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=50)
    price: float = Field(0, ge=0)
    stock: int = Field(0, ge=0)
    status: str = Field("DRAFT", pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")
    description: Optional[str] = Field(None, max_length=5000)
    categoryId: Optional[str] = None
    type: str = Field("RETAIL", pattern=r"^(RETAIL|RENTAL|SERVICE)$")


class UpdateProductRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    sku: Optional[str] = Field(None, max_length=50)
    price: Optional[float] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern=r"^(DRAFT|ACTIVE|ARCHIVED)$")
    description: Optional[str] = Field(None, max_length=5000)
    categoryId: Optional[str] = None
