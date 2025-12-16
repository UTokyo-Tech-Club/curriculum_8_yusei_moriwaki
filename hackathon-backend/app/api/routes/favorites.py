"""
Favorites API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.schemas.favorite import (
    FavoriteAddRequest,
    FavoriteRemoveRequest,
    FavoriteResponse
)
from app.services.favorite_service import FavoriteService
from app.dependencies import get_favorite_service, get_current_user_id

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("/users/{user_id}", response_model=List[int])
async def get_user_favorites(
    user_id: int,
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """Get list of item IDs favorited by a user."""
    favorites = await favorite_service.get_user_favorites(user_id)
    return favorites


@router.post("", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    request: FavoriteAddRequest,
    user_id: int = Depends(get_current_user_id),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """Add an item to favorites (requires authentication)."""
    favorite = await favorite_service.add_favorite(user_id, request.item_id)
    return favorite


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    request: FavoriteRemoveRequest,
    user_id: int = Depends(get_current_user_id),
    favorite_service: FavoriteService = Depends(get_favorite_service)
):
    """Remove an item from favorites (requires authentication)."""
    try:
        await favorite_service.remove_favorite(user_id, request.item_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

