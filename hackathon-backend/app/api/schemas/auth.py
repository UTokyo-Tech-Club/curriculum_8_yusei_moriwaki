"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class RegisterRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    name: str


class LoginRequest(BaseModel):
    """Request schema for login."""
    email: EmailStr


class UserResponse(BaseModel):
    """Response schema for user data."""
    model_config = ConfigDict(populate_by_name=True, by_alias=True)
    
    id: str
    email: str
    name: str
    avatar: Optional[str] = None
    created_at: Optional[str] = Field(None, alias="createdAt")


class AuthResponse(BaseModel):
    """Response schema for authentication (login/register)."""
    user: UserResponse
    token: str

