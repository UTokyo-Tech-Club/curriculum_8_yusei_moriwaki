"""
Pydantic schemas for favorites.
"""
from pydantic import BaseModel
from typing import List, Optional


class FavoriteAddRequest(BaseModel):
    """Request schema for adding a favorite."""
    item_id: int


class FavoriteRemoveRequest(BaseModel):
    """Request schema for removing a favorite."""
    item_id: int


class FavoriteResponse(BaseModel):
    """Response schema for a favorite."""
    id: str
    user_id: str
    item_id: int
    created_at: Optional[str] = None


class FavoriteListResponse(BaseModel):
    """Response schema for list of favorited item IDs."""
    item_ids: List[int]

