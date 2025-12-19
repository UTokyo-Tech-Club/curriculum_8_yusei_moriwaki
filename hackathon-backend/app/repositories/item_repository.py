"""
Item Repository - Data access layer for Item operations.
Joins item_listings with mercari_items for full item details.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item_listing import ItemListing, ListingStatus
from app.models.mercari_item import MercariItem
from app.models.user import User
from app.domain.entities.item import ItemEntity
from app.domain.mappers.item_mapper import ItemMapper


class ItemRepository:
    """Repository for Item data access (joins ItemListing + MercariItem)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_item_with_details(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single item with full details by listing ID.
        Joins item_listings with mercari_items to get complete info.
        """
        # Subquery to get one representative mercari_item per item_id
        subq = (
            select(
                MercariItem.item_id,
                func.min(MercariItem.id).label('min_id')
            )
            .group_by(MercariItem.item_id)
            .subquery()
        )

        result = await self.db.execute(
            select(ItemListing, MercariItem, User)
            .join(subq, ItemListing.item_id == subq.c.item_id)
            .join(MercariItem, and_(
                MercariItem.item_id == ItemListing.item_id,
                MercariItem.id == subq.c.min_id
            ))
            .join(User, ItemListing.seller_user_id == User.id)
            .where(ItemListing.id == listing_id)
        )
        row = result.first()

        if not row:
            return None

        listing, mercari, seller = row
        return self._combine_item_data(listing, mercari, seller)

    async def get_items_with_details(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get multiple items with filters.
        Joins item_listings with mercari_items for full details.
        """
        # Subquery to get one representative mercari_item per item_id
        subq = (
            select(
                MercariItem.item_id,
                func.min(MercariItem.id).label('min_id')
            )
            .group_by(MercariItem.item_id)
            .subquery()
        )

        query = (
            select(ItemListing, MercariItem, User)
            .join(subq, ItemListing.item_id == subq.c.item_id)
            .join(MercariItem, and_(
                MercariItem.item_id == ItemListing.item_id,
                MercariItem.id == subq.c.min_id
            ))
            .join(User, ItemListing.seller_user_id == User.id)
        )

        # Apply filters
        if category:
            # Reverse map frontend category to backend c0_name values
            c0_names = self._reverse_map_category(category)
            if c0_names:
                c0_conditions = [MercariItem.c0_name.ilike(f"%{name}%") for name in c0_names]
                query = query.where(or_(*c0_conditions))
        
        if status:
            if status == "available":
                query = query.where(ItemListing.status == ListingStatus.ACTIVE)
            elif status == "sold":
                query = query.where(ItemListing.status == ListingStatus.SOLD)
        
        if min_price is not None:
            query = query.where(MercariItem.price >= min_price)
        
        if max_price is not None:
            query = query.where(MercariItem.price <= max_price)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    MercariItem.name.ilike(search_pattern),
                    MercariItem.brand_name.ilike(search_pattern),
                    MercariItem.c0_name.ilike(search_pattern)
                )
            )

        # Order by listed_at descending (newest first)
        query = query.order_by(desc(ItemListing.listed_at))
        
        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        rows = result.all()

        return [self._combine_item_data(listing, mercari, seller) for listing, mercari, seller in rows]

    async def get_by_seller(self, seller_user_id: int) -> List[Dict[str, Any]]:
        """Get all items listed by a specific seller."""
        # Subquery for mercari items
        subq = (
            select(
                MercariItem.item_id,
                func.min(MercariItem.id).label('min_id')
            )
            .group_by(MercariItem.item_id)
            .subquery()
        )

        result = await self.db.execute(
            select(ItemListing, MercariItem, User)
            .join(subq, ItemListing.item_id == subq.c.item_id)
            .join(MercariItem, and_(
                MercariItem.item_id == ItemListing.item_id,
                MercariItem.id == subq.c.min_id
            ))
            .join(User, ItemListing.seller_user_id == User.id)
            .where(ItemListing.seller_user_id == seller_user_id)
            .order_by(desc(ItemListing.listed_at))
        )
        rows = result.all()

        return [self._combine_item_data(listing, mercari, seller) for listing, mercari, seller in rows]

    async def get_recommended(
        self, 
        item_id: int, 
        category: str, 
        limit: int = 6,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recommended items from the same category, excluding the given item."""
        # Reverse map frontend category to Mercari c0_name values
        c0_names = self._reverse_map_category(category)
        
        if not c0_names:
            return []
        
        # Subquery to get one representative mercari_item per item_id
        subq = (
            select(
                MercariItem.item_id,
                func.min(MercariItem.id).label('min_id')
            )
            .group_by(MercariItem.item_id)
            .subquery()
        )

        query = (
            select(ItemListing, MercariItem, User)
            .join(subq, ItemListing.item_id == subq.c.item_id)
            .join(MercariItem, and_(
                MercariItem.item_id == ItemListing.item_id,
                MercariItem.id == subq.c.min_id
            ))
            .join(User, ItemListing.seller_user_id == User.id)
        )

        # Filter by multiple c0_names using OR (match any of the category names)
        c0_conditions = [MercariItem.c0_name.ilike(f"%{name}%") for name in c0_names]
        query = query.where(or_(*c0_conditions))
        
        # Search by title (if provided)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    MercariItem.name.ilike(search_pattern),
                    MercariItem.brand_name.ilike(search_pattern),
                    MercariItem.c0_name.ilike(search_pattern)
                )
            )
        
        # Exclude the current item by item_id
        query = query.where(ItemListing.item_id != item_id)
        
        # Only show available items
        query = query.where(ItemListing.status == ListingStatus.ACTIVE)
        
        # Order by listed_at descending (newest first)
        query = query.order_by(desc(ItemListing.listed_at))
        
        # Pagination
        query = query.limit(limit)

        result = await self.db.execute(query)
        rows = result.all()

        return [self._combine_item_data(listing, mercari, seller) for listing, mercari, seller in rows]

    async def create_listing(
        self,
        seller_user_id: int,
        item_id: int,
        product_id: Optional[str] = None
    ) -> ItemListing:
        """Create a new item listing."""
        listing = ItemListing(
            seller_user_id=seller_user_id,
            item_id=item_id,
            product_id=product_id,
            status=ListingStatus.ACTIVE
        )
        self.db.add(listing)
        await self.db.commit()
        await self.db.refresh(listing)
        return listing
    
    async def create_item_with_listing(
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
    ) -> ItemListing:
        """Create a new mercari item and listing."""
        from typing import List
        import random
        
        # Generate a unique item_id
        item_id = random.randint(100000000, 999999999)
        
        # Create the mercari item
        mercari_item = MercariItem(
            item_id=item_id,
            name=title,
            description=description,
            price=price,
            c0_name=category,  # Use c0_name for primary category
            brand_name=brand_name,
            item_condition_name=condition
        )
        self.db.add(mercari_item)
        await self.db.flush()  # Flush to get the id
        
        # Create the listing
        listing = ItemListing(
            seller_user_id=seller_user_id,
            item_id=item_id,
            product_id=f"PROD-{item_id}",
            status=ListingStatus.ACTIVE,
            image_url=image_url
        )
        self.db.add(listing)
        await self.db.commit()
        await self.db.refresh(listing)
        return listing

    async def update_listing(
        self,
        listing_id: int,
        status: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Optional[ItemListing]:
        """Update an item listing."""
        result = await self.db.execute(
            select(ItemListing).where(ItemListing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if not listing:
            return None

        if status:
            listing.status = ListingStatus(status)
        
        if image_url is not None:
            listing.image_url = image_url

        await self.db.commit()
        await self.db.refresh(listing)
        return listing

    async def delete_listing(self, listing_id: int) -> bool:
        """Delete an item listing."""
        result = await self.db.execute(
            select(ItemListing).where(ItemListing.id == listing_id)
        )
        listing = result.scalar_one_or_none()

        if not listing:
            return False

        await self.db.delete(listing)
        await self.db.commit()
        return True

    async def get_listing_by_id(self, listing_id: int) -> Optional[ItemListing]:
        """Get raw ItemListing by ID."""
        result = await self.db.execute(
            select(ItemListing).where(ItemListing.id == listing_id)
        )
        return result.scalar_one_or_none()

    def _combine_item_data(
        self,
        listing: ItemListing,
        mercari: MercariItem,
        seller: User
    ) -> Dict[str, Any]:
        """Combine ItemListing and MercariItem data into a single dict."""
        # Convert image_url to images array for backward compatibility
        images = []
        if listing.image_url:
            images = [listing.image_url]
        
        return {
            "id": str(listing.id),
            "itemId": listing.item_id,
            "title": mercari.name or "No title",
            "name": mercari.name or "No title",  # Alias for embedding service
            "description": mercari.description or mercari.name or "No description",
            "price": float(mercari.price) if mercari.price else 0.0,
            "images": images,
            "category": self._map_category(mercari.c0_name),
            "c0_name": mercari.c0_name,  # For similarity calculation
            "c1_name": mercari.c1_name,  # For similarity calculation
            "c2_name": mercari.c2_name,  # For similarity calculation
            "status": listing.status.value,
            "sellerId": str(listing.seller_user_id),
            "sellerName": seller.name,
            "sellerAvatar": seller.avatar,
            "viewsCount": listing.views_count,
            "likesCount": listing.likes_count,
            "brandName": mercari.brand_name,
            "brand_name": mercari.brand_name,  # Alias for similarity calculation
            "condition": mercari.item_condition_name,
            "item_condition_name": mercari.item_condition_name,  # Alias for similarity calculation
            "size_name": mercari.size_name,  # For similarity calculation
            "createdAt": listing.listed_at.isoformat() if listing.listed_at else None,
            "updatedAt": listing.listed_at.isoformat() if listing.listed_at else None,
        }

    def _map_category(self, c0_name: Optional[str]) -> str:
        """Map mercari category names to frontend category enums."""
        if not c0_name:
            return "other"
        
        category_map = {
            "women": "fashion",
            "men": "fashion",
            "beauty": "fashion",
            "home": "home",
            "sports": "sports",
            "vintage": "other",
        }
        
        c0_lower = c0_name.lower()
        for key, value in category_map.items():
            if key in c0_lower:
                return value
        
        return "other"
    
    def _reverse_map_category(self, category: str) -> List[str]:
        """Reverse map frontend category enum to Mercari c0_name values."""
        reverse_map = {
            "fashion": ["women", "men", "beauty"],
            "home": ["home"],
            "sports": ["sports"],
            "other": ["vintage", "other"]
        }
        return reverse_map.get(category.lower(), ["other"])
    
    async def get_item_with_details_by_item_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single item with full details by item_id (not listing_id).
        Joins item_listings with mercari_items to get complete info.
        """
        # Subquery to get one representative mercari_item per item_id
        subq = (
            select(
                MercariItem.item_id,
                func.min(MercariItem.id).label('min_id')
            )
            .group_by(MercariItem.item_id)
            .subquery()
        )

        result = await self.db.execute(
            select(ItemListing, MercariItem, User)
            .join(subq, ItemListing.item_id == subq.c.item_id)
            .join(MercariItem, and_(
                MercariItem.item_id == ItemListing.item_id,
                MercariItem.id == subq.c.min_id
            ))
            .join(User, ItemListing.seller_user_id == User.id)
            .where(ItemListing.item_id == item_id)
            .limit(1)
        )
        row = result.first()

        if not row:
            return None

        listing, mercari, seller = row
        return self._combine_item_data(listing, mercari, seller)
    
    async def get_items_by_item_ids(self, item_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get multiple items by their item_ids.
        Joins item_listings with mercari_items for full details.
        """
        if not item_ids:
            return []
        
        # Subquery to get one representative mercari_item per item_id
        subq = (
            select(
                MercariItem.item_id,
                func.min(MercariItem.id).label('min_id')
            )
            .group_by(MercariItem.item_id)
            .subquery()
        )

        result = await self.db.execute(
            select(ItemListing, MercariItem, User)
            .join(subq, ItemListing.item_id == subq.c.item_id)
            .join(MercariItem, and_(
                MercariItem.item_id == ItemListing.item_id,
                MercariItem.id == subq.c.min_id
            ))
            .join(User, ItemListing.seller_user_id == User.id)
            .where(ItemListing.item_id.in_(item_ids))
        )
        rows = result.all()

        return [self._combine_item_data(listing, mercari, seller) for listing, mercari, seller in rows]

