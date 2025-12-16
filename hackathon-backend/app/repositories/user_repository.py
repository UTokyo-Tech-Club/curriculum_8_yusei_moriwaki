"""
User Repository - Data access layer for User operations.
"""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.seller_profile import SellerProfile
from app.models.item_listing import ItemListing
from app.models.purchase import Purchase


class UserRepository:
    """Repository for User data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_with_seller_profile(self, user_id: int) -> Optional[User]:
        """Get user with seller profile eagerly loaded."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.seller_profile))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, email: str, name: str, avatar: Optional[str] = None) -> User:
        """Create a new user."""
        # Generate a unique user ID (simple timestamp-based for now)
        import time
        user_id = int(time.time() * 1000) % 9999999999  # Keep it within BIGINT range
        
        user = User(
            id=user_id,
            email=email,
            name=name,
            avatar=avatar
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(
        self,
        user_id: int,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
        bio: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[User]:
        """Update user information."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        if name is not None:
            user.name = name
        if avatar is not None:
            user.avatar = avatar
        if bio is not None:
            user.bio = bio
        if location is not None:
            user.location = location

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_items_count(self, user_id: int) -> int:
        """Get count of items listed by user."""
        result = await self.db.execute(
            select(func.count(ItemListing.id))
            .where(ItemListing.seller_user_id == user_id)
        )
        return result.scalar() or 0

    async def get_purchases_count(self, user_id: int) -> int:
        """Get count of purchases made by user."""
        result = await self.db.execute(
            select(func.count(Purchase.id))
            .where(Purchase.buyer_user_id == user_id)
        )
        return result.scalar() or 0

    async def delete(self, user_id: int) -> bool:
        """Delete a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True

