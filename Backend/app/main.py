from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api import trending, health, analytics

# Import all models to ensure they are registered with Base
from app.models.video import Video
from app.models.country_relevance import CountryRelevance
from app.models.trending_feed import TrendingFeed
from app.models.search_cache import SearchCache
from app.models.training_label import TrainingLabel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting YouTube Trending Analyzer MVP")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Create database tables (skip if they already exist)
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables initialized successfully")
        
        # Manual check and creation for critical tables that might be missing
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if country_relevance table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'country_relevance'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("Creating missing country_relevance table manually")
                conn.execute(text("""
                    CREATE TABLE country_relevance (
                        video_id VARCHAR(20) NOT NULL,
                        country VARCHAR(2) NOT NULL,
                        relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
                        reasoning TEXT,
                        confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
                        origin_country VARCHAR(7) DEFAULT 'UNKNOWN',
                        analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        llm_model VARCHAR(50) DEFAULT 'gemini-flash',
                        PRIMARY KEY (video_id, country),
                        FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
                    );
                """))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_country_score ON country_relevance (country, relevance_score);"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_analyzed_at ON country_relevance (analyzed_at);"))
                conn.commit()
                logger.info("country_relevance table created successfully")
            else:
                logger.info("country_relevance table already exists")
                
    except Exception as e:
        logger.warning(f"Database initialization warning (tables may already exist): {e}")
        # Continue startup even if tables already exist
    
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
allowed_origins = []
if settings.DEBUG:
    allowed_origins = ["*"]
else:
    # Production CORS - allow specific domains
    allowed_origins = [
        "http://localhost:3000",
        "https://localhost:3000",
        "https://youtube-trending-analyzer-mvp-frontend.vercel.app",
        "https://youtube-trending-analyzer-mvp.vercel.app",
        "https://youtube-trending-analyzer.vercel.app"
    ]
    
    # Also allow any vercel.app subdomain for this project
    import re
    def is_vercel_app(origin):
        return re.match(r"https://[a-zA-Z0-9-]+-[a-zA-Z0-9-]+-[a-zA-Z0-9-]+\.vercel\.app$", origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app$" if not settings.DEBUG else None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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