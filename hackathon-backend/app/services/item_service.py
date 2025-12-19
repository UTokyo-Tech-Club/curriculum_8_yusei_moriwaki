"""
Item Service - Business logic for item operations.
"""
from typing import List, Optional, Dict, Any

from app.repositories.item_repository import ItemRepository
from app.repositories.user_repository import UserRepository
from app.utils.image_validator import validate_image_urls
from app.utils.image_generator import generate_image_data_url


class ItemService:
    """Service for item business logic."""

    def __init__(self, item_repo: ItemRepository, user_repo: UserRepository):
        self.item_repo = item_repo
        self.user_repo = user_repo

    async def get_items(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get items with filters."""
        items = await self.item_repo.get_items_with_details(
            category=category,
            status=status,
            min_price=min_price,
            max_price=max_price,
            search=search,
            limit=limit,
            offset=offset
        )
        
        # Generate images for items that don't have any
        for item in items:
            if not item.get("images") or len(item.get("images", [])) == 0:
                title = item.get("title", "Item")
                generated_image_url = generate_image_data_url(title)
                item["images"] = [generated_image_url]
        
        return items

    async def get_item(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """Get a single item by listing ID."""
        item = await self.item_repo.get_item_with_details(listing_id)
        if item and (not item.get("images") or len(item.get("images", [])) == 0):
            # Generate image if missing
            title = item.get("title", "Item")
            generated_image_url = generate_image_data_url(title)
            item["images"] = [generated_image_url]
        return item

    async def get_user_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all items listed by a user."""
        items = await self.item_repo.get_by_seller(user_id)
        
        # Generate images for items that don't have any
        for item in items:
            if not item.get("images") or len(item.get("images", [])) == 0:
                title = item.get("title", "Item")
                generated_image_url = generate_image_data_url(title)
                item["images"] = [generated_image_url]
        
        return items

    async def get_recommended_items(
        self,
        listing_id: int,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """Get recommended items based on an item (same category)."""
        # Get the item to find its category
        item = await self.item_repo.get_item_with_details(listing_id)
        if not item:
            return []

        category = item.get("category", "other")
        item_id = item.get("itemId")  # Use itemId from the combined data
        
        if not item_id:
            return []
        
        # Get items from same category, excluding current item
        # Note: get_recommended already excludes by item_id, but we also filter by listing_id as backup
        items = await self.item_repo.get_recommended(
            item_id=item_id,
            category=category,
            limit=limit + 1  # Get one extra in case current item is in results
        )
        
        # Filter out the current item by listing_id (additional safety check)
        filtered_items = [i for i in items if i["id"] != str(listing_id)][:limit]
        
        # Generate images for items that don't have any
        for item in filtered_items:
            if not item.get("images") or len(item.get("images", [])) == 0:
                title = item.get("title", "Item")
                generated_image_url = generate_image_data_url(title)
                item["images"] = [generated_image_url]
        
        return filtered_items

    async def create_item(
        self,
        seller_user_id: int,
        title: str,
        description: str,
        price: float,
        category: str = "other",
        condition: Optional[str] = "Good",
        brand_name: Optional[str] = None,
        images: List[str] = []
    ) -> Dict[str, Any]:
        """Create a new item and listing."""
        from typing import List
        # Verify seller exists
        seller = await self.user_repo.get_by_id(seller_user_id)
        if not seller:
            raise ValueError("販売者が見つかりません")

        # Create the mercari item and listing together
        listing = await self.item_repo.create_item_with_listing(
            seller_user_id=seller_user_id,
            title=title,
            description=description,
            price=price,
            category=category,
            condition=condition,
            brand_name=brand_name,
            images=images
        )

        # Return full item details
        item = await self.item_repo.get_item_with_details(listing.id)
        if not item:
            raise ValueError("商品の作成に失敗しました")
        
        # Validate image URLs and generate placeholder if all are invalid
        final_images = images.copy() if images else []
        
        if final_images:
            valid_urls, invalid_urls = await validate_image_urls(final_images)
            
            # If all URLs are invalid, generate a seed image
            if not valid_urls:
                # Generate image data URL from title
                generated_image_url = generate_image_data_url(title)
                final_images = [generated_image_url]
            else:
                # Use only valid URLs
                final_images = valid_urls
        else:
            # No images provided, generate one from title
            generated_image_url = generate_image_data_url(title)
            final_images = [generated_image_url]
        
        # Add images to the response (images are not stored in DB yet, so we add them here)
        item["images"] = final_images
        
        return item

    async def update_item(
        self,
        listing_id: int,
        user_id: int,
        status: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an item listing."""
        # Verify ownership
        listing = await self.item_repo.get_listing_by_id(listing_id)
        if not listing:
            raise ValueError("商品が見つかりません")
        
        if listing.seller_user_id != user_id:
            raise PermissionError("この商品を編集する権限がありません")

        # Update listing
        await self.item_repo.update_listing(listing_id, status=status)

        # Return updated item
        item = await self.item_repo.get_item_with_details(listing_id)
        
        # Generate image if missing
        if item and (not item.get("images") or len(item.get("images", [])) == 0):
            title = item.get("title", "Item")
            generated_image_url = generate_image_data_url(title)
            item["images"] = [generated_image_url]
        
        return item

    async def delete_item(self, listing_id: int, user_id: int) -> bool:
        """Delete an item listing."""
        # Verify ownership
        listing = await self.item_repo.get_listing_by_id(listing_id)
        if not listing:
            raise ValueError("商品が見つかりません")
        
        if listing.seller_user_id != user_id:
            raise PermissionError("この商品を削除する権限がありません")

        # Delete listing
        return await self.item_repo.delete_listing(listing_id)

