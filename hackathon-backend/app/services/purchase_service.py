"""
Purchase Service - Business logic for purchase operations.
"""
from typing import List, Optional, Dict, Any

from app.repositories.purchase_repository import PurchaseRepository
from app.repositories.item_repository import ItemRepository
from app.models.item_listing import ListingStatus


class PurchaseService:
    """Service for purchase business logic."""

    def __init__(
        self,
        purchase_repo: PurchaseRepository,
        item_repo: ItemRepository
    ):
        self.purchase_repo = purchase_repo
        self.item_repo = item_repo

    async def create_purchase(
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
    ) -> Dict[str, Any]:
        """Create a new purchase and mark item as sold."""
        # Verify item exists and is available
        listing = await self.item_repo.get_listing_by_id(item_listing_id)
        if not listing:
            raise ValueError("商品が見つかりません")
        
        if listing.status != ListingStatus.ACTIVE:
            raise ValueError("この商品は購入できません")

        # Create purchase
        purchase = await self.purchase_repo.create(
            buyer_user_id=buyer_user_id,
            item_listing_id=item_listing_id,
            payment_method=payment_method,
            shipping_name=shipping_name,
            shipping_postal_code=shipping_postal_code,
            shipping_prefecture=shipping_prefecture,
            shipping_city=shipping_city,
            shipping_address=shipping_address,
            shipping_building=shipping_building,
            shipping_phone=shipping_phone
        )

        # Update item status to sold
        await self.item_repo.update_listing(item_listing_id, status="sold")

        # Get item details
        item = await self.item_repo.get_item_with_details(item_listing_id)

        return {
            "id": str(purchase.id),
            "item_id": str(item_listing_id),
            "item_title": item["title"] if item else "Unknown",
            "item_price": item["price"] if item else 0,
            "item_image": item["images"][0] if item and item["images"] else "",
            "buyer_id": str(purchase.buyer_user_id),
            "seller_id": item["seller_id"] if item else "",
            "status": purchase.status.value,
            "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
            "completed_at": purchase.completed_at.isoformat() if purchase.completed_at else None,
        }

    async def get_purchase(self, purchase_id: int) -> Optional[Dict[str, Any]]:
        """Get a single purchase by ID."""
        purchase = await self.purchase_repo.get_by_id(purchase_id)
        if not purchase:
            return None

        # Get item details
        item = await self.item_repo.get_item_with_details(purchase.item_listing_id)

        return {
            "id": str(purchase.id),
            "item_id": str(purchase.item_listing_id),
            "item_title": item["title"] if item else "Unknown",
            "item_price": item["price"] if item else 0,
            "item_image": item["images"][0] if item and item["images"] else "",
            "buyer_id": str(purchase.buyer_user_id),
            "seller_id": item["seller_id"] if item else "",
            "status": purchase.status.value,
            "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
            "completed_at": purchase.completed_at.isoformat() if purchase.completed_at else None,
        }

    async def get_purchase_history(self, buyer_user_id: int) -> List[Dict[str, Any]]:
        """Get purchase history for a buyer."""
        purchases = await self.purchase_repo.get_by_buyer(buyer_user_id)
        
        result = []
        for purchase in purchases:
            item = await self.item_repo.get_item_with_details(purchase.item_listing_id)
            result.append({
                "id": str(purchase.id),
                "item_id": str(purchase.item_listing_id),
                "item_title": item["title"] if item else "Unknown",
                "item_price": item["price"] if item else 0,
                "item_image": item["images"][0] if item and item["images"] else "",
                "buyer_id": str(purchase.buyer_user_id),
                "seller_id": item["seller_id"] if item else "",
                "status": purchase.status.value,
                "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
                "completed_at": purchase.completed_at.isoformat() if purchase.completed_at else None,
            })
        
        return result

