"""
User domain entity - Framework-agnostic business model for User.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class UserEntity:
    """Domain model for User - framework-agnostic"""
    id: int
    email: str
    name: str
    avatar: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

