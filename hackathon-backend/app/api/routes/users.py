"""
User profile API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.schemas.user import UserProfileResponse, UserProfileUpdateRequest
from app.api.schemas.item import ItemResponse
from app.services.user_service import UserService
from app.services.item_service import ItemService
from app.dependencies import get_user_service, get_item_service, get_current_user_id

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Get user profile with statistics."""
    profile = await user_service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません"
        )
    return profile


@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: int,
    request: UserProfileUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service)
):
    """Update user profile (requires authentication)."""
    # Verify user is updating their own profile
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="他のユーザーのプロフィールは編集できません"
        )

    try:
        profile = await user_service.update_user_profile(
            user_id=user_id,
            name=request.name,
            avatar=request.avatar,
            bio=request.bio,
            location=request.location
        )
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}/items", response_model=List[ItemResponse])
async def get_user_items(
    user_id: int,
    item_service: ItemService = Depends(get_item_service)
):
    """Get all items listed by a user."""
    items = await item_service.get_user_items(user_id)
    return items

