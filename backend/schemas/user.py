from pydantic import BaseModel, Field, ConfigDict, field_validator, computed_field
from typing import Optional, List
from datetime import datetime


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)
    id: str | int # UI sometimes uses numeric IDs
    code: str
    name: str
    description: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v):
        return str(v) if v is not None else None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)
    id: str
    name: str
    code: str
    description: Optional[str] = None
    permissions: List[PermissionResponse] = Field(default_factory=list)

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v):
        return str(v) if v is not None else None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, strict=True)
    id: str
    email: str
    name: str = "Unknown"
    status: str = "ACTIVE"
    roles: List[RoleResponse] = Field(default_factory=list)
    gender: Optional[str] = None
    dob: Optional[datetime] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    extra_metadata: Optional[dict] = Field(default_factory=dict)
    password: Optional[str] = Field(None, exclude=True)
    created_at: datetime

    @computed_field
    @property
    def has_password(self) -> bool:
        """R60: Internal property computed from db model. Note: Pydantic v2 computed_field."""
        # This will be populated from the model if available (via 'password' field above)
        return self.password is not None

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v):
        return str(v) if v is not None else None


class UserListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[UserResponse]
    total: int


class UserUpdatePayload(BaseModel):
    model_config = ConfigDict(strict=True)
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    roles: Optional[List[str]] = None
    gender: Optional[str] = None
    dob: Optional[datetime] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    extra_metadata: Optional[dict] = None


class UserCreatePayload(BaseModel):
    model_config = ConfigDict(strict=True)
    email: str
    name: str
    password: Optional[str] = "SmartShop@123"
    username: Optional[str] = None
    role_codes: List[str] = Field(default_factory=lambda: ["CUSTOMER"])


class UpdatePasswordPayload(BaseModel):
    model_config = ConfigDict(strict=True)
    old_password: Optional[str] = Field(None, min_length=64, max_length=64)
    new_password: str = Field(..., min_length=64, max_length=64)

class PointTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    id: str
    amount: int
    transaction_type: str
    status: str
    notes: Optional[str] = None
    created_at: datetime

class LoyaltyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    tier: str
    available_points: int
    pending_points: int
    total_spent: float
    tier_updated_at: Optional[datetime] = None
    history: List[PointTransactionResponse] = Field(default_factory=list)


class PointAdjustmentRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    amount: int
    notes: str = Field(..., min_length=1, max_length=500)
    transaction_type: str = "ADJUST_ADMIN"
