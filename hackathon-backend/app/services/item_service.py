"""
Item Service - Business logic for item operations.
"""
import logging
from typing import List, Optional, Dict, Any

from app.repositories.item_repository import ItemRepository
from app.repositories.user_repository import UserRepository
from app.utils.image_validator import validate_image_urls
from app.utils.image_generator import generate_image_data_url
from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.services.vector_search_service import VectorSearchService
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)


def _prepare_pinecone_metadata(item: Dict[str, Any]) -> Dict[str, str]:
    """
    Prepare metadata for Pinecone, filtering out None/null values.
    Pinecone does not allow null values in metadata.
    
    Args:
        item: Item dictionary
        
    Returns:
        Dictionary with only non-null metadata values
    """
    metadata = {}
    
    # c0_name
    c0_name = item.get("category") or item.get("c0_name")
    if c0_name:
        metadata["c0_name"] = str(c0_name)
    
    # brand_name
    brand_name = item.get("brandName") or item.get("brand_name")
    if brand_name:
        metadata["brand_name"] = str(brand_name)
    
    # condition
    condition = item.get("condition") or item.get("item_condition_name")
    if condition:
        metadata["condition"] = str(condition)
    
    return metadata


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
        """Get items with filters. Uses SQL search for first 5 items, then vector search for rest."""
        # If search query provided, use hybrid approach
        if search and search.strip():
            items = []
            
            # First 5 items: Use SQL search (like AI chat)
            if offset == 0:
                sql_limit = min(5, limit)
                sql_items = await self.item_repo.get_items_with_details(
                    category=category,
                    status=status,
                    min_price=min_price,
                    max_price=max_price,
                    search=search,
                    limit=sql_limit,
                    offset=0
                )
                items.extend(sql_items)
                
                # If we need more than 5 items, get rest from vector search
                if limit > 5:
                    try:
                        vector_limit = limit - len(items)
                        vector_items = await self.search_items_vector(
                            query=search,
                            category=category,
                            limit=vector_limit * 2  # Get more for filtering
                        )
                        
                        # Apply additional filters (status, price)
                        filtered_vector_items = self._apply_filters(
                            vector_items,
                            status=status,
                            min_price=min_price,
                            max_price=max_price
                        )
                        
                        # Exclude items already in SQL results (by itemId)
                        sql_item_ids = {item.get("itemId") for item in items}
                        unique_vector_items = [
                            item for item in filtered_vector_items
                            if item.get("itemId") not in sql_item_ids
                        ]
                        
                        # Add vector search results
                        items.extend(unique_vector_items[:vector_limit])
                        
                    except Exception as e:
                        logger.warning(f"Vector search failed for additional items: {e}")
                        # Continue with SQL results only
            else:
                # If offset > 0, use vector search for pagination
                try:
                    vector_items = await self.search_items_vector(
                        query=search,
                        category=category,
                        limit=limit * 2  # Get more for filtering
                    )
                    
                    # Apply additional filters
                    filtered_items = self._apply_filters(
                        vector_items,
                        status=status,
                        min_price=min_price,
                        max_price=max_price
                    )
                    
                    items = filtered_items[offset:offset + limit]
                    
                except Exception as e:
                    logger.warning(f"Vector search failed, falling back to SQL search: {e}")
                    items = await self.item_repo.get_items_with_details(
                        category=category,
                        status=status,
                        min_price=min_price,
                        max_price=max_price,
                        search=search,
                        limit=limit,
                        offset=offset
                    )
        else:
            # Use traditional SQL search for non-search queries
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
    
    def _apply_filters(
        self,
        items: List[Dict[str, Any]],
        status: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply filters to a list of items.
        
        Args:
            items: List of item dictionaries
            status: Filter by status (active, sold, etc.)
            min_price: Minimum price filter
            max_price: Maximum price filter
            
        Returns:
            Filtered list of items
        """
        filtered = items
        
        if status:
            if status == "available":
                filtered = [item for item in filtered if item.get("status") == "active"]
            elif status == "sold":
                filtered = [item for item in filtered if item.get("status") == "sold"]
            else:
                filtered = [item for item in filtered if item.get("status") == status]
        
        if min_price is not None:
            filtered = [item for item in filtered if item.get("price", 0) >= min_price]
        
        if max_price is not None:
            filtered = [item for item in filtered if item.get("price", 0) <= max_price]
        
        return filtered

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
        """Get recommended items. First 5 from SQL search, rest from vector/ML search."""
        # Get the item to find its item_id and category
        item = await self.item_repo.get_item_with_details(listing_id)
        if not item:
            return []

        item_id = item.get("itemId")
        if not item_id:
            return []
        
        items = []
        
        # First 5 items: Use SQL search (category-based, like AI chat)
        sql_limit = min(5, limit + 1)  # Get one extra to exclude current item
        try:
            category = item.get("category", "other")
            title = item.get("title", "")
            sql_items = await self.item_repo.get_recommended(
                item_id=item_id,
                category=category,
                limit=sql_limit,
                search=title if title else None
            )
            
            # Filter out the current item by listing_id
            sql_filtered = [i for i in sql_items if i.get("id") != str(listing_id)]
            items.extend(sql_filtered[:5])
            
        except Exception as e:
            logger.warning(f"SQL search for recommendations failed: {e}")
        
        # If we need more than 5 items, get rest from vector search
        if limit > 5 and len(items) < limit:
            try:
                vector_limit = limit - len(items) + 1  # Get one extra to exclude current item
                vector_items = await self.search_items_vector(
                    item_id=item_id,
                    limit=vector_limit
                )
                
                # Filter out the current item and items already in SQL results
                sql_item_ids = {item.get("itemId") for item in items}
                unique_vector_items = [
                    i for i in vector_items
                    if i.get("id") != str(listing_id) and i.get("itemId") not in sql_item_ids
                ]
                
                # Add vector search results
                items.extend(unique_vector_items[:vector_limit - 1])
                
            except Exception as e:
                logger.warning(f"Vector search for additional recommendations failed: {e}")
        
        # Limit to requested amount
        items = items[:limit]
        
        # Generate images for items that don't have any
        for item in items:
            if not item.get("images") or len(item.get("images", [])) == 0:
                title = item.get("title", "Item")
                generated_image_url = generate_image_data_url(title)
                item["images"] = [generated_image_url]
        
        return items

    async def create_item(
        self,
        seller_user_id: int,
        title: str,
        description: str,
        price: float,
        category: str = "other",
        condition: Optional[str] = "Good",
        brand_name: Optional[str] = None,
        images: List[str] = [],
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new item and listing."""
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
            images=images,
            image_url=image_url
        )

        # Return full item details
        item = await self.item_repo.get_item_with_details(listing.id)
        if not item:
            raise ValueError("商品の作成に失敗しました")
        
        # If image_url is provided, use it. Otherwise, validate image URLs or generate placeholder
        if image_url:
            item["images"] = [image_url]
        else:
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
            
            # Add images to the response
            item["images"] = final_images
        
        # Generate and upsert embedding to Pinecone
        try:
            embedding = await embedding_service.generate_item_embedding(item)
            metadata = _prepare_pinecone_metadata(item)
            await pinecone_service.upsert_item_embedding(
                item_id=item["itemId"],
                embedding=embedding,
                metadata=metadata
            )
            logger.info(f"Created embedding for item {item['itemId']}")
        except Exception as e:
            logger.error(f"Error creating embedding for item {item.get('itemId')}: {e}")
            # Don't fail item creation if embedding fails
        
        return item

    async def update_item(
        self,
        listing_id: int,
        user_id: int,
        status: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an item listing."""
        # Verify ownership
        listing = await self.item_repo.get_listing_by_id(listing_id)
        if not listing:
            raise ValueError("商品が見つかりません")
        
        if listing.seller_user_id != user_id:
            raise PermissionError("この商品を編集する権限がありません")

        # Update listing
        await self.item_repo.update_listing(listing_id, status=status, image_url=image_url)

        # Return updated item
        item = await self.item_repo.get_item_with_details(listing_id)
        
        # Generate image if missing
        if item and (not item.get("images") or len(item.get("images", [])) == 0):
            title = item.get("title", "Item")
            generated_image_url = generate_image_data_url(title)
            item["images"] = [generated_image_url]
        
        # Update embedding in Pinecone if item text changed
        if item:
            try:
                embedding = await embedding_service.generate_item_embedding(item)
                metadata = _prepare_pinecone_metadata(item)
                await pinecone_service.upsert_item_embedding(
                    item_id=item["itemId"],
                    embedding=embedding,
                    metadata=metadata
                )
                logger.info(f"Updated embedding for item {item['itemId']}")
            except Exception as e:
                logger.error(f"Error updating embedding for item {item.get('itemId')}: {e}")
                # Don't fail item update if embedding fails
        
        return item

    async def delete_item(self, listing_id: int, user_id: int) -> bool:
        """Delete an item listing."""
        # Verify ownership
        listing = await self.item_repo.get_listing_by_id(listing_id)
        if not listing:
            raise ValueError("商品が見つかりません")
        
        if listing.seller_user_id != user_id:
            raise PermissionError("この商品を削除する権限がありません")

        # Delete embedding from Pinecone
        try:
            item = await self.item_repo.get_item_with_details(listing_id)
            if item and item.get("itemId"):
                await pinecone_service.delete_item_embedding(item["itemId"])
                logger.info(f"Deleted embedding for item {item['itemId']}")
        except Exception as e:
            logger.error(f"Error deleting embedding: {e}")
            # Don't fail item deletion if embedding deletion fails

        # Delete listing
        return await self.item_repo.delete_listing(listing_id)
    
    async def search_items_vector(
        self,
        query: Optional[str] = None,
        item_id: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for items using vector similarity and weighted features.
        
        Args:
            query: Optional text query string
            item_id: Optional item ID to find similar items to
            category: Optional category filter
            limit: Maximum number of results to return
            
        Returns:
            List of item dictionaries sorted by similarity score
        """
        vector_search = VectorSearchService(self.item_repo)
        items = await vector_search.search_similar_items(
            query=query,
            item_id=item_id,
            category=category,
            limit=limit
        )
        
        # Generate images for items that don't have any
        for item in items:
            if not item.get("images") or len(item.get("images", [])) == 0:
                title = item.get("title", "Item")
                generated_image_url = generate_image_data_url(title)
                item["images"] = [generated_image_url]
        
        return items

