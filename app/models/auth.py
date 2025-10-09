"""
Pydantic models for authentication
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """Login request payload"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with JWT token"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    organization_id: str
    role: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TokenData(BaseModel):
    """Decoded JWT token data"""
    user_id: str
    organization_id: str
    role: str
    email: str
