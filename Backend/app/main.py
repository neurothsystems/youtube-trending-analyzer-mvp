from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api import trending, health, analytics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting YouTube Trending Analyzer MVP")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown
    logger.info("Shutting down YouTube Trending Analyzer MVP")


app = FastAPI(
    title="YouTube Trending Analyzer MVP",
    description="LLM-powered platform for genuine regional YouTube trend analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.vercel.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    trending.router,
    prefix="/api/mvp/trending",
    tags=["trending"]
)

app.include_router(
    health.router,
    prefix="/api/mvp",
    tags=["health"]
)

app.include_router(
    analytics.router,
    prefix="/api/mvp/analytics",
    tags=["analytics"]
)


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "message": "YouTube Trending Analyzer MVP API",
        "version": "1.1.0-origin-country",
        "build_info": {
            "commit": "eb10e19",
            "features": [
                "origin_country_detection",
                "multi_tier_search",
                "search_transparency",
                "batch_llm_processing",
                "adaptive_filtering"
            ]
        },
        "docs": "/docs",
        "algorithm": "MVP-LLM-Enhanced",
        "supported_countries": ["DE", "US", "FR", "JP"],
        "supported_timeframes": ["24h", "48h", "7d"]
    }


@app.get("/api/mvp")
async def api_info():
    """API information endpoint."""
    return {
        "api_version": "1.1.0-origin-country",
        "build_commit": "eb10e19",
        "algorithm": "MVP-LLM-Enhanced",
        "llm_provider": "gemini-flash",
        "active_features": {
            "origin_country_detection": True,
            "multi_tier_search": True,
            "search_transparency": True,
            "batch_llm_processing": True,
            "adaptive_filtering": True,
            "cache_invalidation": True
        },
        "supported_countries": {
            "DE": "Germany",
            "US": "USA", 
            "FR": "France",
            "JP": "Japan"
        },
        "timeframes": ["24h", "48h", "7d"],
        "endpoints": {
            "trending": "/api/mvp/trending",
            "health": "/api/mvp/health",
            "analytics": "/api/mvp/analytics",
            "trending_feeds": "/api/mvp/trending-feeds"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )