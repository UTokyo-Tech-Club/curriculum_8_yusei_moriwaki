"""
Item mapper - Converts between dict/ORM models and domain entities.
Note: Items are complex as they combine ItemListing + MercariItem data.
"""
from typing import Dict, Any, Optional
from app.domain.entities.item import ItemEntity


class ItemMapper:
    """Maps between Item dict (from repository) and ItemEntity domain model"""
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ItemEntity:
        """Convert dict (from repository) to domain entity"""
        return ItemEntity(
            id=data.get("id"),
            item_id=data.get("itemId"),
            title=data.get("title", ""),
            price=data.get("price", 0.0),
            description=data.get("description"),
            category=data.get("category"),
            brand=data.get("brand"),
            condition=data.get("condition"),
            images=data.get("images", []),
            seller_id=data.get("sellerId"),
            seller_name=data.get("sellerName", ""),
            seller_avatar=data.get("sellerAvatar"),
            status=data.get("status", "active"),
            views_count=data.get("viewsCount", 0),
            likes_count=data.get("likesCount", 0),
            listed_at=data.get("listedAt")
        )
    
    @staticmethod
    def to_dict(entity: ItemEntity) -> Dict[str, Any]:
        """Convert domain entity to dict for API response"""
        return {
            "id": entity.id,
            "itemId": entity.item_id,
            "title": entity.title,
            "price": entity.price,
            "description": entity.description,
            "category": entity.category,
            "brand": entity.brand,
            "condition": entity.condition,
            "images": entity.images or [],
            "sellerId": entity.seller_id,
            "sellerName": entity.seller_name,
            "sellerAvatar": entity.seller_avatar,
            "status": entity.status,
            "viewsCount": entity.views_count,
            "likesCount": entity.likes_count,
            "listedAt": entity.listed_at.isoformat() if entity.listed_at else None
        }

