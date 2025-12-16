"""
ItemListing model - represents the item_listings table.
"""
from sqlalchemy import Column, Integer, BigInteger, String, TIMESTAMP, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class ListingStatus(str, enum.Enum):
    """Status of an item listing."""
    ACTIVE = "active"
    SOLD = "sold"
    REMOVED = "removed"


class ItemListing(Base):
    """
    ItemListing model - Items posted for sale by users.
    Links to mercari_items for full item details.
    """
    __tablename__ = "item_listings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(BigInteger, nullable=False, unique=True, index=True)
    product_id = Column(String(100), nullable=True)
    listed_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    status = Column(Enum(ListingStatus), default=ListingStatus.ACTIVE, index=True)
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)

    # Relationships
    seller = relationship("User", back_populates="item_listings", foreign_keys=[seller_user_id])
    purchases = relationship(
        "Purchase",
        back_populates="item_listing",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ItemListing(id={self.id}, item_id={self.item_id}, seller_id={self.seller_user_id}, status='{self.status}')>"

