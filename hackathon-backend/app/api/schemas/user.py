"""
Pydantic schemas for user profiles.
"""
from pydantic import BaseModel
from typing import Optional


class UserProfileResponse(BaseModel):
    """Response schema for user profile."""
    id: str
    email: str
    name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[str] = None
    items_count: Optional[int] = 0
    purchases_count: Optional[int] = 0


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""
    name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

