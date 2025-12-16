"""
Configuration module for the application.
Loads environment variables and provides database URL.
"""
import os
from typing import Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database configuration
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PWD: str = os.getenv("MYSQL_PWD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "hackathon")
    
    # Database SSL certificates (for Cloud SQL)
    MYSQL_SSL_CA: Optional[str] = os.getenv("MYSQL_SSL_CA")
    MYSQL_SSL_CERT: Optional[str] = os.getenv("MYSQL_SSL_CERT")
    MYSQL_SSL_KEY: Optional[str] = os.getenv("MYSQL_SSL_KEY")
    
    # JWT Configuration (dummy)
    JWT_SECRET_KEY: str = "dummy-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct async database URL for SQLAlchemy."""
        # URL-encode username and password to handle special characters like @ and !
        user = quote_plus(self.MYSQL_USER)
        pwd = quote_plus(self.MYSQL_PWD)
        return f"mysql+aiomysql://{user}:{pwd}@{self.MYSQL_HOST}/{self.MYSQL_DATABASE}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Construct sync database URL for Alembic migrations."""
        # URL-encode username and password to handle special characters like @ and !
        user = quote_plus(self.MYSQL_USER)
        pwd = quote_plus(self.MYSQL_PWD)
        return f"mysql+pymysql://{user}:{pwd}@{self.MYSQL_HOST}/{self.MYSQL_DATABASE}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

