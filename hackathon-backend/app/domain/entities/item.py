"""
Item domain entity - Framework-agnostic business model for Item.
Represents the combined data from ItemListing and MercariItem.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class ItemEntity:
    """Domain model for Item - framework-agnostic"""
    # Core item info
    id: int  # listing_id
    item_id: int  # mercari item_id
    title: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    condition: Optional[str] = None
    images: Optional[List[str]] = None
    
    # Listing info
    seller_id: int
    seller_name: str
    seller_avatar: Optional[str] = None
    status: str = "active"
    views_count: int = 0
    likes_count: int = 0
    listed_at: Optional[datetime] = None

