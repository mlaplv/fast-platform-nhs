from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class HealthStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    system: str = "Fast-Platform Gateway"
    status: str = "online"

class AnomalyItem(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    type: str
    message: str
    time: str

class AnomalyResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    count: int
    anomalies: List[AnomalyItem]
