from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
 
class ChatMessageSchema(BaseModel):
    id: str
    session_id: str
    user_id: Optional[str] = None
    role: str
    content: Dict[str, Any]  # R25: JSONB typed - Supports nested metadata (Rule R86)
    modality: str
    created_at: datetime
    updated_at: datetime

class CreateChatMessageRequest(BaseModel):
    role: str  # "user" | "assistant"
    content: Dict[str, Any]
    modality: str = "text"

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageSchema]
    next_cursor: Optional[str] = None
    has_more: bool = False

