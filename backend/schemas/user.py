from pydantic import BaseModel, Field, ConfigDict, field_validator
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
    createdAt: datetime = Field(alias="created_at")

    @field_validator("id", mode="before")
    @classmethod
    def stringify_id(cls, v):
        return str(v) if v is not None else None


class UserListResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: List[UserResponse]
    total: int
