"""
Pydantic schemas for favorites.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class FavoriteAddRequest(BaseModel):
    """Request schema for adding a favorite."""
    item_id: int


class FavoriteRemoveRequest(BaseModel):
    """Request schema for removing a favorite."""
    item_id: int


class FavoriteResponse(BaseModel):
    """Response schema for a favorite."""
    model_config = ConfigDict(populate_by_name=True, by_alias=True)
    
    id: str
    user_id: str = Field(alias="userId")
    item_id: int = Field(alias="itemId")
    created_at: Optional[str] = Field(None, alias="createdAt")


class FavoriteListResponse(BaseModel):
    """Response schema for list of favorited item IDs."""
    item_ids: List[int]

