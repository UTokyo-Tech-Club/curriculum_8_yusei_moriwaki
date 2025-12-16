"""
Favorite Repository - Data access layer for Favorite operations.
"""
from typing import List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.favorite import Favorite


class FavoriteRepository:
    """Repository for Favorite data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_favorites(self, user_id: int) -> List[int]:
        """Get list of item IDs favorited by a user."""
        result = await self.db.execute(
            select(Favorite.item_id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.favorited_at.desc())
        )
        return [row[0] for row in result.all()]

    async def add_favorite(self, user_id: int, item_id: int) -> Favorite:
        """Add an item to user's favorites."""
        # Check if already exists
        existing = await self.get_favorite(user_id, item_id)
        if existing:
            return existing

        favorite = Favorite(user_id=user_id, item_id=item_id)
        self.db.add(favorite)
        await self.db.commit()
        await self.db.refresh(favorite)
        return favorite

    async def remove_favorite(self, user_id: int, item_id: int) -> bool:
        """Remove an item from user's favorites."""
        result = await self.db.execute(
            select(Favorite).where(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.item_id == item_id
                )
            )
        )
        favorite = result.scalar_one_or_none()

        if not favorite:
            return False

        await self.db.delete(favorite)
        await self.db.commit()
        return True

    async def get_favorite(self, user_id: int, item_id: int) -> Favorite | None:
        """Get a specific favorite."""
        result = await self.db.execute(
            select(Favorite).where(
                and_(
                    Favorite.user_id == user_id,
                    Favorite.item_id == item_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def is_favorited(self, user_id: int, item_id: int) -> bool:
        """Check if an item is favorited by a user."""
        favorite = await self.get_favorite(user_id, item_id)
        return favorite is not None

