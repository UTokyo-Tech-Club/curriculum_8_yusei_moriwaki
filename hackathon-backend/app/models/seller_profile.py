"""
SellerProfile model - represents the user_seller_profiles table.
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, DECIMAL, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class SellerProfile(Base):
    """
    SellerProfile model - Optional seller information for users.
    """
    __tablename__ = "user_seller_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    shop_name = Column(String(255), nullable=False, index=True)
    shop_description = Column(Text, nullable=True)
    rating = Column(DECIMAL(3, 2), default=5.00)
    total_sales = Column(Integer, default=0)
    total_listings = Column(Integer, default=0)
    joined_as_seller_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="seller_profile")

    def __repr__(self):
        return f"<SellerProfile(id={self.id}, user_id={self.user_id}, shop_name='{self.shop_name}')>"



