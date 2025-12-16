"""
SQLAlchemy Base model and database session configuration.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


# SQLAlchemy declarative base
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Create async engine
# No SSL needed when using Cloud SQL Proxy - it handles the secure connection
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Disable SQL logging for better performance
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,  # Maintain 5 connections in the pool
    max_overflow=10,  # Allow up to 10 additional connections
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

