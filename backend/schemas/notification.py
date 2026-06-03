from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)

    id: str
    userId: Optional[str] = Field(None, alias="user_id")
    type: str = "INFO"
    message: str
    isRead: bool = Field(False, alias="is_read")
    createdAt: datetime = Field(alias="created_at")

    @field_validator("id", "userId", mode="before")
    @classmethod
    def stringify_ids(cls, v):
        return str(v) if v is not None else None


class NotificationListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[NotificationResponse]
    total: int


class NotificationCursorPaginatedResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[NotificationResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False

