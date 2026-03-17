from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict

class KeyStats(BaseModel):
    model_config = ConfigDict(strict=True)
    index: int
    key_preview: str = Field(alias="key_preview")
    fail_count: int = Field(alias="fail_count")
    health_score: int = Field(alias="health_score")
    last_used: float = Field(alias="last_used")
    status: str

class BulkKeyInput(BaseModel):
    model_config = ConfigDict(strict=True)
    keys: str

class ModelConfig(BaseModel):
    model_config = ConfigDict(strict=True)
    primary_model: Optional[str] = Field(None, alias="primary_model")
    ai_models: List[str] = Field(default_factory=list, alias="ai_models")

class AIModelStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True, populate_by_name=True)
    primary_model: str = Field(alias="primary_model")
    ai_models: List[str] = Field(alias="ai_models")
    discovered_models: List[str] = Field(alias="discovered_models")

class ModelDiscoveryResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    models: List[str]
