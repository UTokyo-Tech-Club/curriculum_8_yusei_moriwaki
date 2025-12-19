"""
Favorite model - represents the user_favorites table.
"""
from sqlalchemy import Column, Integer, BigInteger, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Favorite(Base):
    """
    Favorite model - Items that users have favorited/liked.
    """
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(BigInteger, nullable=False, index=True)
    favorited_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    user = relationship("User", back_populates="favorites")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'item_id', name='unique_favorite'),
    )

    def __repr__(self):
        return f"<Favorite(id={self.id}, user_id={self.user_id}, item_id={self.item_id})>"




