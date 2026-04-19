from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

class VoucherBase(BaseModel):
    id: str = Field(..., description="Voucher Code (e.g. SALE30K)")
    type: str = Field("FIXED", description="FIXED, PERCENT, SHIPPING")
    title: Optional[str] = None
    subtitle: Optional[str] = None
    value: float = Field(0.0)
    min_spend: float = Field(0.0)
    max_discount: Optional[float] = None
    usage_limit: Optional[int] = None
    used_count: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    category: str = Field("DISCOUNT")
    is_default: bool = Field(False)
    priority: int = Field(0)

class CreateVoucherRequest(VoucherBase):
    pass

class UpdateVoucherRequest(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    value: Optional[float] = None
    min_spend: Optional[float] = None
    max_discount: Optional[float] = None
    usage_limit: Optional[int] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category: Optional[str] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None

class VoucherResponse(VoucherBase):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime
    updated_at: datetime

class VoucherListResponse(BaseModel):
    data: List[VoucherResponse]
    total: int
