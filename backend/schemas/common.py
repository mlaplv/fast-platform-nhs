from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, List

class SuccessResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    ok: bool = True
    message: Optional[str] = None
    id: Optional[str] = None
    data: Optional[Any] = None

class BulkActionResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    ok: bool = True
    count: int = 0

class BulkIdsRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    ids: List[str] = Field(..., min_length=1, max_length=100)
