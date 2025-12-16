"""
Purchase Repository - Data access layer for Purchase operations.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.purchase import Purchase


class PurchaseRepository:
    """Repository for Purchase data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        buyer_user_id: int,
        item_listing_id: int,
        payment_method: str,
        shipping_name: str,
        shipping_postal_code: str,
        shipping_prefecture: str,
        shipping_city: str,
        shipping_address: str,
        shipping_building: Optional[str],
        shipping_phone: str
    ) -> Purchase:
        """Create a new purchase."""
        purchase = Purchase(
            buyer_user_id=buyer_user_id,
            item_listing_id=item_listing_id,
            payment_method=payment_method,
            shipping_name=shipping_name,
            shipping_postal_code=shipping_postal_code,
            shipping_prefecture=shipping_prefecture,
            shipping_city=shipping_city,
            shipping_address=shipping_address,
            shipping_building=shipping_building,
            shipping_phone=shipping_phone,
            status='completed',  # Auto-complete for dummy implementation
            completed_at=datetime.utcnow()
        )
        self.db.add(purchase)
        await self.db.commit()
        await self.db.refresh(purchase)
        return purchase

    async def get_by_id(self, purchase_id: int) -> Optional[Purchase]:
        """Get purchase by ID with related data."""
        result = await self.db.execute(
            select(Purchase)
            .options(
                selectinload(Purchase.buyer),
                selectinload(Purchase.item_listing)
            )
            .where(Purchase.id == purchase_id)
        )
        return result.scalar_one_or_none()

    async def get_by_buyer(self, buyer_user_id: int) -> List[Purchase]:
        """Get all purchases by a buyer."""
        result = await self.db.execute(
            select(Purchase)
            .options(
                selectinload(Purchase.item_listing)
            )
            .where(Purchase.buyer_user_id == buyer_user_id)
            .order_by(Purchase.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_seller(self, seller_user_id: int) -> List[Purchase]:
        """Get all purchases of items sold by a seller."""
        result = await self.db.execute(
            select(Purchase)
            .join(Purchase.item_listing)
            .options(
                selectinload(Purchase.buyer),
                selectinload(Purchase.item_listing)
            )
            .where(Purchase.item_listing.has(seller_user_id=seller_user_id))
            .order_by(Purchase.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, purchase_id: int, status: str) -> Optional[Purchase]:
        """Update purchase status."""
        result = await self.db.execute(
            select(Purchase).where(Purchase.id == purchase_id)
        )
        purchase = result.scalar_one_or_none()

        if not purchase:
            return None

        purchase.status = PurchaseStatus(status)
        if status == "completed" and not purchase.completed_at:
            purchase.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(purchase)
        return purchase

