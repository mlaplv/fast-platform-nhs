from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    # R25: Use strict Regex instead of EmailStr to allow internal '.test' domains while preventing injection
    identifier: str = Field(..., pattern=r"^[a-zA-Z0-9_.@+-]+$", max_length=254)
    password: str = Field(..., min_length=64, max_length=64)  # SHA-256 hex = exactly 64 chars
    remember_me: bool = Field(default=False)

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
    request_id: Optional[str] = None

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

class SocialLoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    token: str
    platform: Optional[str] = None
    metadata: Optional[dict] = None

class OTPRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_.@+-]+$")

class OTPVerifyRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    phone: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    otp_token: str
    code: str = Field(..., min_length=6, max_length=6)
