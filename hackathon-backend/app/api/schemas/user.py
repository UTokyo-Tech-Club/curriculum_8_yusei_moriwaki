"""
Pydantic schemas for user profiles.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class UserProfileResponse(BaseModel):
    """Response schema for user profile."""
    model_config = ConfigDict(populate_by_name=True, by_alias=True)
    
    id: str
    email: str
    name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[str] = Field(None, alias="createdAt")
    items_count: Optional[int] = Field(0, alias="itemsCount")
    purchases_count: Optional[int] = Field(0, alias="purchasesCount")


class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile."""
    name: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

