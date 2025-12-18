"""
Purchase mapper - Converts between ORM models and domain entities.
"""
from typing import Optional
from app.models.purchase import Purchase as PurchaseORM
from app.domain.entities.purchase import PurchaseEntity


class PurchaseMapper:
    """Maps between Purchase ORM model and PurchaseEntity domain model"""
    
    @staticmethod
    def to_domain(orm: Optional[PurchaseORM]) -> Optional[PurchaseEntity]:
        """Convert ORM model to domain entity"""
        if orm is None:
            return None
            
        return PurchaseEntity(
            id=orm.id,
            buyer_user_id=orm.buyer_user_id,
            item_listing_id=orm.item_listing_id,
            payment_method=str(orm.payment_method),
            shipping_name=orm.shipping_name,
            shipping_postal_code=orm.shipping_postal_code,
            shipping_prefecture=orm.shipping_prefecture,
            shipping_city=orm.shipping_city,
            shipping_address=orm.shipping_address,
            shipping_building=orm.shipping_building,
            shipping_phone=orm.shipping_phone,
            status=str(orm.status),
            created_at=orm.created_at,
            completed_at=orm.completed_at
        )
    
    @staticmethod
    def to_orm(entity: PurchaseEntity) -> PurchaseORM:
        """Convert domain entity to ORM model"""
        return PurchaseORM(
            id=entity.id,
            buyer_user_id=entity.buyer_user_id,
            item_listing_id=entity.item_listing_id,
            payment_method=entity.payment_method,
            shipping_name=entity.shipping_name,
            shipping_postal_code=entity.shipping_postal_code,
            shipping_prefecture=entity.shipping_prefecture,
            shipping_city=entity.shipping_city,
            shipping_address=entity.shipping_address,
            shipping_building=entity.shipping_building,
            shipping_phone=entity.shipping_phone,
            status=entity.status
        )

