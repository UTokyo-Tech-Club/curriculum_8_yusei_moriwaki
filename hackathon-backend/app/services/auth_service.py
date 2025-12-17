"""
Auth Service - Business logic for authentication.
Dummy implementation with no password verification.
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt

from app.config import settings
from app.repositories.user_repository import UserRepository


class AuthService:
    """Service for authentication logic (dummy implementation)."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, email: str, name: str) -> dict:
        """
        Register a new user (dummy - no password required).
        Returns user and JWT token.
        """
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("このメールアドレスは既に登録されています")

        # Create new user
        user = await self.user_repo.create(email=email, name=name)

        # Generate JWT token
        token = self._create_token(user.id)

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "avatar": user.avatar,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
            "token": token
        }

    async def login(self, email: str) -> dict:
        """
        Login user (dummy - no password verification).
        Returns user and JWT token if email exists.
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("ユーザーが見つかりません")

        # Generate JWT token
        token = self._create_token(user.id)

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "avatar": user.avatar,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
            "token": token
        }

    async def get_current_user(self, user_id: int) -> Optional[dict]:
        """Get current user from JWT token."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "avatar": user.avatar,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    def _create_token(self, user_id: int) -> str:
        """Create JWT token (dummy implementation)."""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=settings.JWT_EXPIRATION_DAYS)
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)



