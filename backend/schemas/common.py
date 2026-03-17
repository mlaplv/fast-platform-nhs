from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, TypeVar, Generic

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(strict=True)
    ok: bool = True
    message: Optional[str] = None
    id: Optional[str] = None
    data: Optional[T] = None

class BulkActionResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    ok: bool = True
    count: int = 0

class BulkIdsRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ids: List[str] = Field(..., min_length=1, max_length=100)
