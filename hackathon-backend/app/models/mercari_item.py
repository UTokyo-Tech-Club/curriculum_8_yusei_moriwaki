"""
MercariItem model - represents the mercari_items table.
Contains rich item metadata and user interaction events.
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, DECIMAL, DateTime, TIMESTAMP
from sqlalchemy.sql import func

from app.models.base import Base


class MercariItem(Base):
    """
    MercariItem model - User interactions with items (views, likes, purchases).
    Contains full item details like name, price, category, brand, etc.
    """
    __tablename__ = "mercari_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True, index=True)  # User viewing/interacting
    stime = Column(DateTime, nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    sequence_id = Column(String(100), nullable=True)
    sequence_length = Column(Integer, nullable=True)
    event_id = Column(String(50), nullable=True, index=True)  # item_view, item_like, buy_comp, etc.
    
    # Item details
    item_id = Column(BigInteger, nullable=False, index=True)
    product_id = Column(String(100), nullable=True)
    name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    
    # Category information
    c0_name = Column(String(255), nullable=True, index=True)
    c0_id = Column(Integer, nullable=True)
    c1_name = Column(String(255), nullable=True, index=True)
    c1_id = Column(Integer, nullable=True)
    c2_name = Column(String(255), nullable=True)
    c2_id = Column(Integer, nullable=True)
    
    # Brand information
    brand_name = Column(String(255), nullable=True, index=True)
    brand_id = Column(Integer, nullable=True)
    
    # Item condition
    item_condition_id = Column(Integer, nullable=True)
    item_condition_name = Column(String(100), nullable=True)
    
    # Size and color
    size_name = Column(String(255), nullable=True)
    size_id = Column(Integer, nullable=True)
    color = Column(String(255), nullable=True)
    
    # Shipping
    shipper_id = Column(Integer, nullable=True)
    shipper_name = Column(String(100), nullable=True)
    
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    def __repr__(self):
        return f"<MercariItem(id={self.id}, item_id={self.item_id}, event='{self.event_id}', name='{self.name}')>"

