from pydantic import BaseModel
from typing import Optional
class CreateUserSchema(BaseModel):
    username: str
    email: str
    phone_number: Optional[str] = None
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    phone_number: Optional[str] = None
    role: str
    is_active: bool
    is_staff: bool
    
    class Config:
        from_attributes = True
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int