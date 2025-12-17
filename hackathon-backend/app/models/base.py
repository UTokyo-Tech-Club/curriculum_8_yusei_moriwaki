"""
Database base configuration.
Defines the Base class and database engine/session setup.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Create async engine
# Note: aiomysql only supports connect_timeout, not read_timeout or write_timeout
# Timeout management is handled by pool_pre_ping, pool_recycle, and MySQL session settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,  # Check connection validity before use (timeout prevention)
    pool_recycle=300,     # Re-establish connections every 5 minutes (timeout prevention)
    pool_size=5,
    max_overflow=10,
    connect_args={
        "connect_timeout": 10,  # Only timeout parameter supported by aiomysql
    },
)

# Set MySQL session timeouts on connection
@event.listens_for(engine.sync_engine, "connect")
def set_mysql_timeout(dbapi_conn, connection_record):
    """Set MySQL session timeouts to prevent connection loss."""
    try:
        with dbapi_conn.cursor() as cursor:
            cursor.execute("SET SESSION wait_timeout = 28800")
            cursor.execute("SET SESSION interactive_timeout = 28800")
            cursor.execute("SELECT 1")
    except Exception as e:
        logger.warning(f"Failed to set MySQL timeouts: {e}")

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)