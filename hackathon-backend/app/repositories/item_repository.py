"""
Item Repository - Data access layer for Item operations.
Joins item_listings with mercari_items for full item details.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.item_listing import ItemListing, ListingStatus
from app.models.mercari_item import MercariItem
from app.models.user import User


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
            query = query.where(MercariItem.c0_name.ilike(f"%{category}%"))
        
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

    async def get_recommended(self, item_id: int, category: str, limit: int = 6) -> List[Dict[str, Any]]:
        """Get recommended items from the same category, excluding the given item."""
        return await self.get_items_with_details(
            category=category,
            status="available",
            limit=limit
        )

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
        images: List[str] = []
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
            price=int(price),
            category_name=category,
            brand_name=brand_name,
            item_condition_name=condition,
            num_likes=0,
            num_comments=0
        )
        self.db.add(mercari_item)
        await self.db.flush()  # Flush to get the id
        
        # Create the listing
        listing = ItemListing(
            seller_user_id=seller_user_id,
            item_id=item_id,
            product_id=f"PROD-{item_id}",
            status=ListingStatus.ACTIVE
        )
        self.db.add(listing)
        await self.db.commit()
        await self.db.refresh(listing)
        return listing

    async def update_listing(
        self,
        listing_id: int,
        status: Optional[str] = None
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
        return {
            "id": str(listing.id),
            "item_id": listing.item_id,
            "title": mercari.name or "No title",
            "description": mercari.name or "No description",
            "price": float(mercari.price) if mercari.price else 0.0,
            "images": [],  # Placeholder - no images in DB yet
            "category": self._map_category(mercari.c0_name),
            "status": listing.status.value,
            "seller_id": str(listing.seller_user_id),
            "seller_name": seller.name,
            "seller_avatar": seller.avatar,
            "views_count": listing.views_count,
            "likes_count": listing.likes_count,
            "brand_name": mercari.brand_name,
            "condition": mercari.item_condition_name,
            "created_at": listing.listed_at.isoformat() if listing.listed_at else None,
            "updated_at": listing.listed_at.isoformat() if listing.listed_at else None,
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

