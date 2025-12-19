"""
Items API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import List, Optional

from app.api.schemas.item import (
    ItemResponse,
    ItemCreateRequest,
    ItemUpdateRequest,
)
from app.services.item_service import ItemService
from app.dependencies import get_item_service, get_current_user_id
from app.utils.image_generator import generate_item_image

router = APIRouter(prefix="/items", tags=["Items"])


@router.get("", response_model=List[ItemResponse])
async def get_items(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    item_service: ItemService = Depends(get_item_service)
):
    """Get items with filters."""
    items = await item_service.get_items(
        category=category,
        status=status,
        min_price=min_price,
        max_price=max_price,
        search=search,
        limit=limit,
        offset=offset
    )
    return items


@router.get("/{listing_id}", response_model=ItemResponse)
async def get_item(
    listing_id: int,
    item_service: ItemService = Depends(get_item_service)
):
    """Get a single item by listing ID."""
    item = await item_service.get_item(listing_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="商品が見つかりません"
        )
    return item


@router.get("/{listing_id}/recommended", response_model=List[ItemResponse])
async def get_recommended_items(
    listing_id: int,
    limit: int = Query(6, le=20),
    item_service: ItemService = Depends(get_item_service)
):
    """Get recommended items (same category)."""
    items = await item_service.get_recommended_items(listing_id, limit=limit)
    return items


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    request: ItemCreateRequest,
    user_id: int = Depends(get_current_user_id),
    item_service: ItemService = Depends(get_item_service)
):
    """Create a new item listing (requires authentication)."""
    try:
        item = await item_service.create_item(
            seller_user_id=user_id,
            title=request.title,
            description=request.description,
            price=request.price,
            category=request.category,
            condition=request.condition,
            brand_name=request.brand_name,
            images=request.images
        )
        return item
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{listing_id}", response_model=ItemResponse)
async def update_item(
    listing_id: int,
    request: ItemUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    item_service: ItemService = Depends(get_item_service)
):
    """Update an item listing (requires authentication and ownership)."""
    try:
        item = await item_service.update_item(
            listing_id=listing_id,
            user_id=user_id,
            status=request.status
        )
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="商品が見つかりません"
            )
        return item
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    listing_id: int,
    user_id: int = Depends(get_current_user_id),
    item_service: ItemService = Depends(get_item_service)
):
    """Delete an item listing (requires authentication and ownership)."""
    try:
        success = await item_service.delete_item(listing_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="商品が見つかりません"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/generated-image/{title:path}")
async def get_generated_image(
    title: str,
    width: int = Query(800, ge=100, le=2000),
    height: int = Query(800, ge=100, le=2000)
):
    """
    Generate a placeholder image for an item based on its title.
    Returns a PNG image with a solid color background and centered title text.
    """
    try:
        image_bytes = generate_item_image(title, width, height)
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=31536000"}  # Cache for 1 year
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"画像の生成に失敗しました: {str(e)}"
        )


@router.get("/search/vector", response_model=List[ItemResponse])
async def vector_search_items(
    query: Optional[str] = Query(None, description="Text query for semantic search"),
    item_id: Optional[int] = Query(None, description="Item ID to find similar items to"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    limit: int = Query(10, le=50, description="Maximum number of results"),
    item_service: ItemService = Depends(get_item_service)
):
    """
    Search for items using vector similarity and weighted ML features.
    
    Either 'query' or 'item_id' must be provided.
    """
    if not query and not item_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'query' or 'item_id' must be provided"
        )
    
    try:
        items = await item_service.search_items_vector(
            query=query,
            item_id=item_id,
            category=category,
            limit=limit
        )
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )

