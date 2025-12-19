"""
Dependency injection for FastAPI routes.
Provides database sessions, services, and authentication.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.config import settings
from app.models.base import async_session_maker
from app.repositories.user_repository import UserRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.purchase_repository import PurchaseRepository
from app.services.auth_service import AuthService
from app.services.item_service import ItemService
from app.services.favorite_service import FavoriteService
from app.services.user_service import UserService
from app.services.purchase_service import PurchaseService


# ============================================================================
# Database Session Dependency
# ============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================================================
# Repository Dependencies
# ============================================================================

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Provide UserRepository instance."""
    return UserRepository(db)


async def get_item_repository(db: AsyncSession = Depends(get_db)) -> ItemRepository:
    """Provide ItemRepository instance."""
    return ItemRepository(db)


async def get_favorite_repository(db: AsyncSession = Depends(get_db)) -> FavoriteRepository:
    """Provide FavoriteRepository instance."""
    return FavoriteRepository(db)


async def get_purchase_repository(db: AsyncSession = Depends(get_db)) -> PurchaseRepository:
    """Provide PurchaseRepository instance."""
    return PurchaseRepository(db)


# ============================================================================
# Service Dependencies
# ============================================================================

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Provide AuthService instance."""
    return AuthService(user_repo)


async def get_item_service(
    item_repo: ItemRepository = Depends(get_item_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> ItemService:
    """Provide ItemService instance."""
    return ItemService(item_repo, user_repo)


async def get_favorite_service(
    favorite_repo: FavoriteRepository = Depends(get_favorite_repository)
) -> FavoriteService:
    """Provide FavoriteService instance."""
    return FavoriteService(favorite_repo)


async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Provide UserService instance."""
    return UserService(user_repo)


async def get_purchase_service(
    purchase_repo: PurchaseRepository = Depends(get_purchase_repository),
    item_repo: ItemRepository = Depends(get_item_repository)
) -> PurchaseService:
    """Provide PurchaseService instance."""
    return PurchaseService(purchase_repo, item_repo)


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user_id(
    authorization: Optional[str] = Header(None)
) -> int:
    """
    Extract user ID from JWT token (dummy implementation).
    No password verification - accepts any valid JWT.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証が必要です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効な認証スキームです",
            )
        
        # Decode JWT token (dummy - no password check)
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無効なトークンです",
            )
        
        return user_id
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効な認証ヘッダーです",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンの有効期限が切れています",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンの検証に失敗しました",
        )


async def get_optional_user_id(
    authorization: Optional[str] = Header(None)
) -> Optional[int]:
    """
    Extract user ID from JWT token if present, otherwise return None.
    Used for endpoints that work with or without authentication.
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user_id(authorization)
    except HTTPException:
        return None



