"""
Pydantic schemas for purchases.
"""
from pydantic import BaseModel
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
    payment_method: PaymentMethod
    shipping_address: ShippingAddressRequest


class PurchaseResponse(BaseModel):
    """Response schema for purchase data."""
    id: str
    item_id: str
    item_title: str
    item_price: float
    item_image: str
    buyer_id: str
    seller_id: str
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

