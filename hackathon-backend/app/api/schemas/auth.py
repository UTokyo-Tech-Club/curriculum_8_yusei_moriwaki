"""
Pydantic schemas for authentication.
"""
from pydantic import BaseModel, EmailStr
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
    id: str
    email: str
    name: str
    avatar: Optional[str] = None
    created_at: Optional[str] = None


class AuthResponse(BaseModel):
    """Response schema for authentication (login/register)."""
    user: UserResponse
    token: str

