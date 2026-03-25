from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AppointmentType(str, Enum):
    STRATEGY = "STRATEGY"
    DEPLOYMENT = "DEPLOYMENT"
    REVIEW = "REVIEW"

class AppointmentStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"

class AppointmentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    type: AppointmentType = AppointmentType.STRATEGY
    status: AppointmentStatus = AppointmentStatus.UPCOMING
    recurring_type: str = "none"
    recurring_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    campaign_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    type: Optional[AppointmentType] = None
    status: Optional[AppointmentStatus] = None
    recurring_type: Optional[str] = None
    recurring_metadata: Optional[Dict[str, Any]] = None
    campaign_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class AppointmentResponse(AppointmentBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class AppointmentListResponse(BaseModel):
    items: List[AppointmentResponse]
    total: int
