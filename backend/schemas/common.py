from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, TypeVar, Generic, NewType

# Elite V2.2: Extreme Type Safety with NewType for IDs
TenantID = NewType("TenantID", str)
OrderID = NewType("OrderID", str)
UserID = NewType("UserID", str)
SessionID = NewType("SessionID", str)
CampaignID = NewType("CampaignID", str)

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(strict=True)
    ok: bool = True
    success: bool = True # Elite V2.2: Compatibility with storefront ".success" checks
    message: Optional[str] = None
    id: Optional[str] = None
    data: Optional[T] = None

class BulkActionResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    ok: bool = True
    count: int = 0
    skipped: List[str] = Field(default_factory=list)  # IDs bị từ chối (có sản phẩm/con)

class BulkIdsRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ids: List[str] = Field(..., min_length=1, max_length=100)

class BulkStatusRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ids: List[str] = Field(..., min_length=1, max_length=100)
    active: bool = True

