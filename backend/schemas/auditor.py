from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Optional

class RiskMetric(BaseModel):
    model_config = ConfigDict(strict=True)
    label: str
    score: float = Field(..., ge=0, le=100)
    reason: str

class ImpactForecast(BaseModel):
    model_config = ConfigDict(strict=True)
    category: str
    impact_level: str  # "LOW", "MEDIUM", "HIGH"
    description: str

class AuditorAnalysisResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    draft_id: str
    overall_risk_score: float = Field(..., ge=0, le=100)
    risk_metrics: List[RiskMetric]
    impact_forecasts: List[ImpactForecast]
    recommendation: str
    timestamp: str
