from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from backend.schemas.product import ProductResponse
from backend.schemas.promotion import VoucherResponse
from backend.schemas.system_settings import SystemSettingsPayload
from backend.schemas.category import CategoryResponse
from backend.schemas.banner import BannerResponse

class HomeVideoSchema(BaseModel):
    """Elite V2.2: Schema for viral storefront videos."""
    id: str
    title: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    order_index: int = 0

class HomeDataResponse(BaseModel):
    """Elite V2.2: Unified Home Data Schema (Strict Typing - NO 'Any')."""
    model_config = ConfigDict(from_attributes=True)
    
    banners: List[BannerResponse]
    categories: List[CategoryResponse]
    products: List[ProductResponse]
    ai_products: List[ProductResponse]
    vouchers: List[VoucherResponse]
    settings: SystemSettingsPayload = Field(default_factory=SystemSettingsPayload)
    videos: List[HomeVideoSchema] = []
