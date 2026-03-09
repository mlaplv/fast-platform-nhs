from pydantic import BaseModel, Field
from typing import Optional

class LoginRequest(BaseModel):
    # R25: Use strict Regex instead of EmailStr to allow internal '.test' domains while preventing injection
    identifier: str = Field(..., pattern=r"^[a-zA-Z0-9_.@+-]+$", max_length=254)
    password: str = Field(..., min_length=64, max_length=64)  # SHA-256 hex = exactly 64 chars

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    role: str
    name: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    role: str

class RegisterRequest(BaseModel):
    name: str = Field(...)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.@+-]+$", max_length=254)
    password: str = Field(..., min_length=6, max_length=64)
