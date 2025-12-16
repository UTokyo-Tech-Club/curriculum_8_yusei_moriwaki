"""
Pydantic schemas for items.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum


class ItemCategory(str, Enum):
    """Item category enum."""
    FASHION = "fashion"
    ELECTRONICS = "electronics"
    BOOKS = "books"
    SPORTS = "sports"
    HOME = "home"
    OTHER = "other"


class ItemStatus(str, Enum):
    """Item status enum."""
    AVAILABLE = "available"
    SOLD = "sold"
    RESERVED = "reserved"


class ItemFilters(BaseModel):
    """Query parameters for filtering items."""
    category: Optional[str] = None
    status: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0


class ItemCreateRequest(BaseModel):
    """Request schema for creating an item."""
    title: str
    description: str
    price: float
    category: str = "other"
    condition: Optional[str] = "Good"
    brand_name: Optional[str] = None
    images: List[str] = []


class ItemUpdateRequest(BaseModel):
    """Request schema for updating an item."""
    status: Optional[str] = None


class ItemResponse(BaseModel):
    """Response schema for item data."""
    model_config = ConfigDict(populate_by_name=True, by_alias=True)
    
    id: str
    item_id: int = Field(alias="itemId")
    title: str
    description: str
    price: float
    images: List[str]
    category: str
    status: str
    seller_id: str = Field(alias="sellerId")
    seller_name: str = Field(alias="sellerName")
    seller_avatar: Optional[str] = Field(None, alias="sellerAvatar")
    views_count: int = Field(alias="viewsCount")
    likes_count: int = Field(alias="likesCount")
    brand_name: Optional[str] = Field(None, alias="brandName")
    condition: Optional[str] = None
    created_at: Optional[str] = Field(None, alias="createdAt")
    updated_at: Optional[str] = Field(None, alias="updatedAt")

