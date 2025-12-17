"""
Purchase API routes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.schemas.purchase import PurchaseCreateRequest, PurchaseResponse
from app.services.purchase_service import PurchaseService
from app.dependencies import get_purchase_service, get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.post("", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
async def create_purchase(
    request: PurchaseCreateRequest,
    user_id: int = Depends(get_current_user_id),
    purchase_service: PurchaseService = Depends(get_purchase_service)
):
    """Create a new purchase (requires authentication)."""
    logger.debug(
        f"Received purchase request - item_id: {request.item_id}, "
        f"payment_method: {request.payment_method}, user_id: {user_id}"
    )
    try:
        purchase = await purchase_service.create_purchase(
            buyer_user_id=user_id,
            item_listing_id=request.item_id,
            payment_method=request.payment_method,
            shipping_name=request.shipping_address.name,
            shipping_postal_code=request.shipping_address.postal_code,
            shipping_prefecture=request.shipping_address.prefecture,
            shipping_city=request.shipping_address.city,
            shipping_address=request.shipping_address.address,
            shipping_building=request.shipping_address.building,
            shipping_phone=request.shipping_address.phone
        )
        return purchase
    except ValueError as e:
        logger.warning(f"ValueError in create_purchase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_purchase: {type(e).__name__}: {str(e)}", exc_info=True)
        raise


@router.get("/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(
    purchase_id: int,
    user_id: int = Depends(get_current_user_id),
    purchase_service: PurchaseService = Depends(get_purchase_service)
):
    """Get a single purchase (requires authentication)."""
    purchase = await purchase_service.get_purchase(purchase_id)
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="購入情報が見つかりません"
        )
    
    # Verify user owns this purchase
    if purchase["buyer_id"] != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この購入情報にアクセスする権限がありません"
        )
    
    return purchase


@router.get("/users/{user_id}", response_model=List[PurchaseResponse])
async def get_purchase_history(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    purchase_service: PurchaseService = Depends(get_purchase_service)
):
    """Get purchase history for a user (requires authentication)."""
    # Verify user is accessing their own history
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="他のユーザーの購入履歴は閲覧できません"
        )
    
    purchases = await purchase_service.get_purchase_history(user_id)
    return purchases

