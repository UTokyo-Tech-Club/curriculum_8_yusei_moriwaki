"""
FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import auth, items, users, favorites, purchases, delta
from app.services.pinecone_service import pinecone_service
from app.services.ml_weights_service import ml_weights_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting up application...")
    
    # Initialize Pinecone
    try:
        await pinecone_service.initialize()
        logger.info("Pinecone initialized successfully")
    except Exception as e:
        logger.warning(f"Pinecone initialization failed: {e}. Vector search will be disabled.")
    
    # ML weights are loaded on import, just log
    weights = ml_weights_service.get_all_weights()
    if weights:
        logger.info(f"ML weights loaded: {len(weights)} features")
    else:
        logger.warning("No ML weights loaded. Using default weights.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")

# Create FastAPI app
app = FastAPI(
    title="Hackathon Backend API",
    description="4-layer architecture backend with FastAPI, SQLAlchemy, and Alembic",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(items.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(favorites.router, prefix=settings.API_V1_PREFIX)
app.include_router(purchases.router, prefix=settings.API_V1_PREFIX)
app.include_router(delta.router)  # Delta router already has /api/delta prefix


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Hackathon Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "api": settings.API_V1_PREFIX
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "hackathon-backend"}

