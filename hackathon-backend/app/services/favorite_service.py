"""
Favorite Service - Business logic for favorite operations.
"""
from typing import List

from app.repositories.favorite_repository import FavoriteRepository


class FavoriteService:
    """Service for favorite business logic."""

    def __init__(self, favorite_repo: FavoriteRepository):
        self.favorite_repo = favorite_repo

    async def get_user_favorites(self, user_id: int) -> List[int]:
        """Get list of item IDs favorited by a user."""
        return await self.favorite_repo.get_user_favorites(user_id)

    async def add_favorite(self, user_id: int, item_id: int) -> dict:
        """Add an item to user's favorites."""
        favorite = await self.favorite_repo.add_favorite(user_id, item_id)
        
        return {
            "id": str(favorite.id),
            "user_id": str(favorite.user_id),
            "item_id": favorite.item_id,
            "created_at": favorite.favorited_at.isoformat() if favorite.favorited_at else None,
        }

    async def remove_favorite(self, user_id: int, item_id: int) -> bool:
        """Remove an item from user's favorites."""
        success = await self.favorite_repo.remove_favorite(user_id, item_id)
        if not success:
            raise ValueError("お気に入りが見つかりません")
        return True

    async def is_favorited(self, user_id: int, item_id: int) -> bool:
        """Check if an item is favorited by a user."""
        return await self.favorite_repo.is_favorited(user_id, item_id)



