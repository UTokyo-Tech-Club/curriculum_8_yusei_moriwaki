"""
Purchase domain entity - Framework-agnostic business model for Purchase.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class PurchaseEntity:
    """Domain model for Purchase - framework-agnostic"""
    id: int
    buyer_user_id: int
    item_listing_id: int
    
    # Payment information
    payment_method: str  # 'credit', 'bank', 'convenience'
    
    # Shipping information
    shipping_name: str
    shipping_postal_code: str
    shipping_prefecture: str
    shipping_city: str
    shipping_address: str
    shipping_building: Optional[str] = None
    shipping_phone: str = ""
    
    # Status and timestamps
    status: str = "pending"  # 'pending', 'completed', 'cancelled'
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

