"""
User model - represents the users table.
"""
from sqlalchemy import Column, BigInteger, String, TIMESTAMP, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class User(Base):
    """
    User model - All users (buyers and sellers).
    """
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    avatar = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # Relationships
    seller_profile = relationship(
        "SellerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    item_listings = relationship(
        "ItemListing",
        back_populates="seller",
        foreign_keys="ItemListing.seller_user_id",
        cascade="all, delete-orphan"
    )
    favorites = relationship(
        "Favorite",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    purchases = relationship(
        "Purchase",
        back_populates="buyer",
        foreign_keys="Purchase.buyer_user_id",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"

