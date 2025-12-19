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
    MYSQL_HOST: str = "term8-yusei-moriwaki:us-central1:uttc"
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
    
    # Pinecone Configuration
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: str = "hackathon-items"
    PINECONE_ENVIRONMENT: Optional[str] = None  # For older Pinecone accounts
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI embedding model (1536 dimensions)
    
    # ML Weights Configuration
    ML_WEIGHTS_PATH: Optional[str] = None  # Path to results JSON file
    
    # Similarity Blend Weights
    VECTOR_WEIGHT: float = 0.6  # Weight for vector similarity (α)
    FEATURE_WEIGHT: float = 0.4  # Weight for ML features (β)
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None  # Service role key for server-side operations
    SUPABASE_BUCKET_NAME: str = "item-images"  # Public bucket name for item images
    
    # CORS - Can be set via environment variable as comma-separated string
    # Example: CORS_ORIGINS="http://localhost:3000,https://hackathon-frontend-roan.vercel.app"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,https://hackathon-frontend-roan.vercel.app"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list."""
        if isinstance(self.CORS_ORIGINS, str):
            # Split by comma and strip whitespace
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            return origins
        elif isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        else:
            return ["http://localhost:3000"]
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct async database URL for SQLAlchemy."""
        # URL-encode username and password to handle special characters like @ and !
        user = quote_plus(self.MYSQL_USER)
        pwd = quote_plus(self.MYSQL_PWD)
        
        # Handle Cloud SQL connection strings (format: PROJECT_ID:REGION:INSTANCE_NAME)
        # Convert to Unix socket path format for Cloud Run
        host = self.MYSQL_HOST
        if ":" in host and not host.startswith("/") and not host.startswith("localhost") and not host.startswith("127.0.0.1"):
            # This is a Cloud SQL connection string, use Unix socket with localhost
            socket_path = f"/cloudsql/{host}"
            return f"mysql+aiomysql://{user}:{pwd}@localhost/{self.MYSQL_DATABASE}?unix_socket={quote_plus(socket_path)}"
        
        return f"mysql+aiomysql://{user}:{pwd}@{host}/{self.MYSQL_DATABASE}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Construct sync database URL for Alembic migrations."""
        # URL-encode username and password to handle special characters like @ and !
        user = quote_plus(self.MYSQL_USER)
        pwd = quote_plus(self.MYSQL_PWD)
        
        # Handle Cloud SQL connection strings (format: PROJECT_ID:REGION:INSTANCE_NAME)
        # Convert to Unix socket path format for Cloud Run
        host = self.MYSQL_HOST
        if ":" in host and not host.startswith("/") and not host.startswith("localhost") and not host.startswith("127.0.0.1"):
            # This is a Cloud SQL connection string, use Unix socket with localhost
            socket_path = f"/cloudsql/{host}"
            return f"mysql+pymysql://{user}:{pwd}@localhost/{self.MYSQL_DATABASE}?unix_socket={quote_plus(socket_path)}"
        
        return f"mysql+pymysql://{user}:{pwd}@{host}/{self.MYSQL_DATABASE}"


# Global settings instance
settings = Settings()

