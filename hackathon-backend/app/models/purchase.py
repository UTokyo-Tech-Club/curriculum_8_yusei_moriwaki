"""
Purchase model - represents the purchases table (new table to be created).
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, TIMESTAMP, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class PaymentMethod(str, enum.Enum):
    """Payment method for a purchase."""
    CREDIT = "credit"
    BANK = "bank"
    CONVENIENCE = "convenience"


class PurchaseStatus(str, enum.Enum):
    """Status of a purchase."""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Purchase(Base):
    """
    Purchase model - Tracks item purchases with shipping and payment info.
    """
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_listing_id = Column(Integer, ForeignKey("item_listings.id", ondelete="CASCADE"), nullable=False)
    
    # Payment information
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    
    # Shipping information
    shipping_name = Column(String(255), nullable=False)
    shipping_postal_code = Column(String(20), nullable=False)
    shipping_prefecture = Column(String(100), nullable=False)
    shipping_city = Column(String(255), nullable=False)
    shipping_address = Column(Text, nullable=False)
    shipping_building = Column(String(255), nullable=True)
    shipping_phone = Column(String(50), nullable=False)
    
    # Status and timestamps
    status = Column(Enum(PurchaseStatus), default=PurchaseStatus.PENDING, index=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    buyer = relationship("User", back_populates="purchases", foreign_keys=[buyer_user_id])
    item_listing = relationship("ItemListing", back_populates="purchases")

    def __repr__(self):
        return f"<Purchase(id={self.id}, buyer_id={self.buyer_user_id}, listing_id={self.item_listing_id}, status='{self.status}')>"

