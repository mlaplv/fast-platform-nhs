from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class BannerBase(BaseModel):
    title: str
    description: Optional[str] = None
    image_url: str
    link_url: Optional[str] = None
    position: str = "home_main"
    order_index: int = 0
    is_active: bool = True
    device_type: str = "all"

class CreateBannerRequest(BannerBase):
    pass

class UpdateBannerRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    position: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None
    device_type: Optional[str] = None

class BannerResponse(BannerBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime
    updated_at: datetime

class BannerListResponse(BaseModel):
    data: List[BannerResponse]
    total: int
