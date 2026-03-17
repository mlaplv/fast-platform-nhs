from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    # R25: Use strict Regex instead of EmailStr to allow internal '.test' domains while preventing injection
    identifier: str = Field(..., pattern=r"^[a-zA-Z0-9_.@+-]+$", max_length=254)
    password: str = Field(..., min_length=64, max_length=64)  # SHA-256 hex = exactly 64 chars

class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    access_token: str
    token_type: str = "Bearer"
    role: str
    name: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)
    id: str
    email: str
    role: str

class SocialLoginResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    message: str
    instructions: str

class OTPRequestResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    message: str
    otp_token: str

class OTPVerifyResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str = "success"
    access_token: str
    role: str

class RegisterRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    email: str
    name: str
    password: str
