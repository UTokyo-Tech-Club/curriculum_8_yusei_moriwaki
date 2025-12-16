"""
Pydantic schemas for purchases.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum


class PaymentMethod(str, Enum):
    """Payment method enum."""
    CREDIT = "credit"
    BANK = "bank"
    CONVENIENCE = "convenience"


class PurchaseStatus(str, Enum):
    """Purchase status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ShippingAddressRequest(BaseModel):
    """Shipping address schema."""
    postal_code: str
    prefecture: str
    city: str
    address: str
    building: Optional[str] = None
    name: str
    phone: str


class PurchaseCreateRequest(BaseModel):
    """Request schema for creating a purchase."""
    item_id: int
    payment_method: str  # 'credit', 'bank', or 'convenience'
    shipping_address: ShippingAddressRequest


class PurchaseResponse(BaseModel):
    """Response schema for purchase data."""
    model_config = ConfigDict(populate_by_name=True, by_alias=True)
    
    id: str
    item_id: str = Field(alias="itemId")
    item_title: str = Field(alias="itemTitle")
    item_price: float = Field(alias="itemPrice")
    item_image: str = Field(alias="itemImage")
    buyer_id: str = Field(alias="buyerId")
    seller_id: str = Field(alias="sellerId")
    status: str
    created_at: Optional[str] = Field(None, alias="createdAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")

