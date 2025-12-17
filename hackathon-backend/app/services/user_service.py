"""
User Service - Business logic for user profile operations.
"""
from typing import Optional

from app.repositories.user_repository import UserRepository


class UserService:
    """Service for user business logic."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_user_profile(self, user_id: int) -> Optional[dict]:
        """Get user profile with statistics."""
        user = await self.user_repo.get_with_seller_profile(user_id)
        if not user:
            return None

        # Get statistics
        items_count = await self.user_repo.get_items_count(user_id)
        purchases_count = await self.user_repo.get_purchases_count(user_id)

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
            "bio": user.bio,
            "location": user.location,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
            "itemsCount": items_count,
            "purchasesCount": purchases_count,
        }

    async def update_user_profile(
        self,
        user_id: int,
        name: Optional[str] = None,
        avatar: Optional[str] = None,
        bio: Optional[str] = None,
        location: Optional[str] = None
    ) -> Optional[dict]:
        """Update user profile."""
        user = await self.user_repo.update(
            user_id=user_id,
            name=name,
            avatar=avatar,
            bio=bio,
            location=location
        )
        
        if not user:
            raise ValueError("ユーザーが見つかりません")

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
            "bio": user.bio,
            "location": user.location,
            "createdAt": user.created_at.isoformat() if user.created_at else None,
        }

