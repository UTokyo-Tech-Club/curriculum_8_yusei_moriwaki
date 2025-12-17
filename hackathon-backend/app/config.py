"""
Configuration module for the application.
Loads environment variables and provides database URL.
"""
from typing import Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )
    
    # Database configuration
    MYSQL_HOST: str = "localhost"
    MYSQL_USER: str = "root"
    MYSQL_PWD: str = ""
    MYSQL_DATABASE: str = "hackathon"
    
    # Database SSL certificates (for Cloud SQL)
    MYSQL_SSL_CA: Optional[str] = None
    MYSQL_SSL_CERT: Optional[str] = None
    MYSQL_SSL_KEY: Optional[str] = None
    
    # JWT Configuration (dummy)
    JWT_SECRET_KEY: str = "dummy-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 7
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    
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


# Global settings instance
settings = Settings()

