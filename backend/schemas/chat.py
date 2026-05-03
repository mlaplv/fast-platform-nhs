from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, Dict, Union, List

class ChatMessageSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)
    id: str
    sessionId: str = Field(..., alias="session_id")
    userId: Optional[str] = Field(None, alias="user_id")
    role: str
    content: Dict[str, object]  # R25: JSONB typed - Supports nested metadata (Rule R86)
    modality: str
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(default_factory=datetime.now, alias="updated_at")

    @field_validator("id", "sessionId", "userId", mode="before")
    @classmethod
    def stringify_ids(cls, v):
        return str(v) if v is not None else None

    @field_validator("createdAt", "updatedAt", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                if v.endswith('Z'):
                    v = v[:-1] + '+00:00'
                return datetime.fromisoformat(v)
            except ValueError:
                pass
        return v

class CreateChatMessageRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    role: str  # "user" | "assistant"
    content: Dict[str, object]
    modality: str = "text"

class ChatHistoryResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    session_id: str
    messages: list[ChatMessageSchema]
    next_cursor: Optional[str] = None
    has_more: bool = False

