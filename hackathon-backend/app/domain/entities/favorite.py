"""
Favorite domain entity - Framework-agnostic business model for Favorite.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class FavoriteEntity:
    """Domain model for Favorite - framework-agnostic"""
    id: int
    user_id: int
    item_id: int
    favorited_at: Optional[datetime] = None

