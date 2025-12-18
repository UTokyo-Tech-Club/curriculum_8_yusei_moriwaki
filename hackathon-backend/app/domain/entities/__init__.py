"""Domain entities - Framework-agnostic business models."""

from app.domain.entities.user import UserEntity
from app.domain.entities.item import ItemEntity
from app.domain.entities.purchase import PurchaseEntity
from app.domain.entities.favorite import FavoriteEntity

__all__ = [
    "UserEntity",
    "ItemEntity",
    "PurchaseEntity",
    "FavoriteEntity",
]

