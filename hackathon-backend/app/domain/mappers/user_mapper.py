"""
User mapper - Converts between ORM models and domain entities.
"""
from typing import Optional
from app.models.user import User as UserORM
from app.domain.entities.user import UserEntity


class UserMapper:
    """Maps between User ORM model and UserEntity domain model"""
    
    @staticmethod
    def to_domain(orm: Optional[UserORM]) -> Optional[UserEntity]:
        """Convert ORM model to domain entity"""
        if orm is None:
            return None
            
        return UserEntity(
            id=orm.id,
            email=orm.email,
            name=orm.name,
            avatar=orm.avatar,
            bio=orm.bio,
            location=orm.location,
            created_at=orm.created_at,
            updated_at=orm.updated_at
        )
    
    @staticmethod
    def to_orm(entity: UserEntity) -> UserORM:
        """Convert domain entity to ORM model"""
        return UserORM(
            id=entity.id,
            email=entity.email,
            name=entity.name,
            avatar=entity.avatar,
            bio=entity.bio,
            location=entity.location
        )

