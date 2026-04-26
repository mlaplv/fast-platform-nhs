from enum import Enum
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class PromptCategory(str, Enum):
    CORE = "core"
    MIXIN = "mixin"
    AGENT = "agent"
    NICHE = "niche"
    SHIELD = "shield"
    INSTRUCTION = "instruction"
    GUIDELINE = "guideline"

class PromptComponent(BaseModel):
    id: str
    category: PromptCategory
    content: str
    version: str = "2.2"
    metadata: Dict[str, str] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

class PromptTemplate(BaseModel):
    name: str
    components: List[str]  # List of component IDs to assemble
    description: Optional[str] = None
