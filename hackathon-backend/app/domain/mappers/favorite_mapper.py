"""
Favorite mapper - Converts between ORM models and domain entities.
"""
from typing import Optional
from app.models.favorite import Favorite as FavoriteORM
from app.domain.entities.favorite import FavoriteEntity


class FavoriteMapper:
    """Maps between Favorite ORM model and FavoriteEntity domain model"""
    
    @staticmethod
    def to_domain(orm: Optional[FavoriteORM]) -> Optional[FavoriteEntity]:
        """Convert ORM model to domain entity"""
        if orm is None:
            return None
            
        return FavoriteEntity(
            id=orm.id,
            user_id=orm.user_id,
            item_id=orm.item_id,
            favorited_at=orm.favorited_at
        )
    
    @staticmethod
    def to_orm(entity: FavoriteEntity) -> FavoriteORM:
        """Convert domain entity to ORM model"""
        return FavoriteORM(
            id=entity.id,
            user_id=entity.user_id,
            item_id=entity.item_id
        )

