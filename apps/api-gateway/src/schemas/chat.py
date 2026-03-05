from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Union
 
class ChatMessageSchema(BaseModel):
    id: str
    session_id: str
    user_id: Optional[str] = None
    role: str
    content: Dict[str, Union[str, int, bool, float, None]]  # R25: JSONB typed
    modality: str
    created_at: datetime
    updated_at: datetime

class CreateChatMessageRequest(BaseModel):
    role: str  # "user" | "assistant"
    content: Dict[str, Union[str, int, bool, float, None]]
    modality: str = "text"

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessageSchema]
    next_cursor: Optional[str] = None
    has_more: bool = False

