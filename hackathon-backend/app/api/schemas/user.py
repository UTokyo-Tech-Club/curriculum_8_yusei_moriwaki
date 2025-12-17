"""
Pydantic schemas for user profiles.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class UserProfileResponse(BaseModel):
    """Response schema for user profile."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    email: str
    name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    createdAt: Optional[str] = None
    itemsCount: Optional[int] = 0
    purchasesCount: Optional[int] = 0


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""
    name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

