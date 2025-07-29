from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from sqlalchemy import text
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
from app.models.llm_usage_log import LLMUsageLog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting YouTube Trending Analyzer MVP")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local'}")
    
    # Create database tables (skip if they already exist)
    try:
        # First, test database connection
        logger.info("Testing database connection...")
        with engine.connect() as test_conn:
            result = test_conn.execute(text("SELECT 1"))
            logger.info(f"Database connection successful: {result.scalar()}")
        
        # Try SQLAlchemy table creation first
        logger.info("Attempting SQLAlchemy table creation...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("SQLAlchemy table creation completed")
        
        # Manual table creation for missing tables with detailed logging
        logger.info("Starting manual table creation verification...")
        
        # Use a transaction to ensure all-or-nothing table creation
        with engine.begin() as conn:
            # Create all tables step by step if they don't exist
            tables_to_create = [
                {
                    'name': 'videos',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS videos (
                            video_id VARCHAR(20) PRIMARY KEY,
                            title TEXT NOT NULL,
                            channel_name VARCHAR(255),
                            channel_country VARCHAR(2),
                            views INTEGER DEFAULT 0,
                            likes INTEGER DEFAULT 0,
                            comments INTEGER DEFAULT 0,
                            upload_date TIMESTAMP WITH TIME ZONE,
                            last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            duration INTEGER,
                            thumbnail_url TEXT,
                            description TEXT,
                            tags JSON
                        );
                    """,
                    'indexes': [
                        "CREATE INDEX IF NOT EXISTS idx_upload_date ON videos (upload_date);",
                        "CREATE INDEX IF NOT EXISTS idx_channel_country ON videos (channel_country);",
                        "CREATE INDEX IF NOT EXISTS idx_views ON videos (views);",
                        "CREATE INDEX IF NOT EXISTS idx_last_updated ON videos (last_updated);"
                    ]
                },
                {
                    'name': 'country_relevance',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS country_relevance (
                            video_id VARCHAR(20) NOT NULL,
                            country VARCHAR(2) NOT NULL,
                            relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
                            reasoning TEXT,
                            confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
                            origin_country VARCHAR(7) DEFAULT 'UNKNOWN',
                            analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            llm_model VARCHAR(50) DEFAULT 'gemini-flash',
                            PRIMARY KEY (video_id, country)
                        );
                    """,
                    'indexes': [
                        "CREATE INDEX IF NOT EXISTS idx_country_score ON country_relevance (country, relevance_score);",
                        "CREATE INDEX IF NOT EXISTS idx_analyzed_at ON country_relevance (analyzed_at);",
                        "CREATE INDEX IF NOT EXISTS idx_video_country ON country_relevance (video_id, country);"
                    ]
                },
                {
                    'name': 'trending_feeds',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS trending_feeds (
                            id SERIAL PRIMARY KEY,
                            video_id VARCHAR(20) NOT NULL,
                            country VARCHAR(2) NOT NULL,
                            trending_rank INTEGER,
                            category VARCHAR(50),
                            captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """,
                    'indexes': [
                        "CREATE INDEX IF NOT EXISTS idx_country_captured ON trending_feeds (country, captured_at);",
                        "CREATE INDEX IF NOT EXISTS idx_video_trending ON trending_feeds (video_id);",
                        "CREATE INDEX IF NOT EXISTS idx_country_rank_captured ON trending_feeds (country, trending_rank, captured_at);"
                    ]
                },
                {
                    'name': 'search_cache',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS search_cache (
                            cache_key VARCHAR(255) PRIMARY KEY,
                            query VARCHAR(255),
                            country VARCHAR(2),
                            timeframe VARCHAR(20),
                            results JSON NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP WITH TIME ZONE
                        );
                    """,
                    'indexes': [
                        "CREATE INDEX IF NOT EXISTS idx_expires ON search_cache (expires_at);",
                        "CREATE INDEX IF NOT EXISTS idx_query_country_timeframe ON search_cache (query, country, timeframe);",
                        "CREATE INDEX IF NOT EXISTS idx_created_at ON search_cache (created_at);"
                    ]
                },
                {
                    'name': 'training_labels',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS training_labels (
                            id SERIAL PRIMARY KEY,
                            video_id VARCHAR(20) NOT NULL,
                            country VARCHAR(2) NOT NULL,
                            query VARCHAR(255),
                            is_relevant BOOLEAN NOT NULL,
                            relevance_score FLOAT,
                            reasoning TEXT,
                            labeled_by VARCHAR(50) DEFAULT 'admin',
                            labeled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """,
                    'indexes': [
                        "CREATE INDEX IF NOT EXISTS idx_training_country ON training_labels (country);",
                        "CREATE INDEX IF NOT EXISTS idx_video_country_training ON training_labels (video_id, country);",
                        "CREATE INDEX IF NOT EXISTS idx_labeled_at ON training_labels (labeled_at);",
                        "CREATE INDEX IF NOT EXISTS idx_query ON training_labels (query);"
                    ]
                },
                {
                    'name': 'llm_usage_log',
                    'sql': """
                        CREATE TABLE IF NOT EXISTS llm_usage_log (
                            id SERIAL PRIMARY KEY,
                            request_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
                            model_name VARCHAR(50) NOT NULL,
                            input_tokens INTEGER NOT NULL,
                            output_tokens INTEGER NOT NULL,
                            cost_usd NUMERIC(10, 6) NOT NULL,
                            cost_eur NUMERIC(10, 6),
                            exchange_rate NUMERIC(8, 4),
                            country VARCHAR(2),
                            query VARCHAR(255),
                            video_count INTEGER,
                            processing_time_ms INTEGER,
                            cache_hit VARCHAR(10),
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """,
                    'indexes': [
                        "CREATE INDEX IF NOT EXISTS idx_llm_request_id ON llm_usage_log (request_id);",
                        "CREATE INDEX IF NOT EXISTS idx_llm_model_name ON llm_usage_log (model_name);",
                        "CREATE INDEX IF NOT EXISTS idx_llm_country ON llm_usage_log (country);",
                        "CREATE INDEX IF NOT EXISTS idx_llm_created_at ON llm_usage_log (created_at);"
                    ]
                }
            ]
            
            # First, check which tables already exist
            logger.info("Checking existing tables...")
            try:
                existing_tables = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)).fetchall()
                existing_table_names = [row[0] for row in existing_tables]
                logger.info(f"Existing tables: {existing_table_names}")
            except Exception as e:
                logger.warning(f"Could not check existing tables: {e}")
                existing_table_names = []
            
            # Create tables one by one with detailed logging and better error handling
            for table in tables_to_create:
                table_name = table['name']
                try:
                    if table_name in existing_table_names:
                        logger.info(f"Table {table_name} already exists, skipping creation")
                        continue
                        
                    logger.info(f"Creating table {table_name}...")
                    
                    # Execute table creation SQL with proper error handling
                    conn.execute(text(table['sql']))
                    logger.info(f"Table {table_name} created successfully")
                    
                    # Create indexes with individual error handling
                    logger.info(f"Creating indexes for table {table_name}...")
                    for i, index_sql in enumerate(table['indexes']):
                        try:
                            conn.execute(text(index_sql))
                            logger.info(f"Index {i+1}/{len(table['indexes'])} created for {table_name}")
                        except Exception as idx_error:
                            logger.warning(f"Non-critical: Error creating index {i+1} for {table_name}: {idx_error}")
                            # Continue with other indexes even if one fails
                    
                    logger.info(f"✅ Table {table_name} and indexes processed successfully")
                    
                except Exception as e:
                    logger.error(f"❌ Error creating table {table_name}: {e}")
                    logger.error(f"SQL that failed: {table['sql'][:200]}...")
                    # Since we're using engine.begin(), the transaction will automatically rollback on exception
                    raise  # Re-raise to trigger transaction rollback
            
            # Final verification - check which tables exist after creation
            logger.info("Final table verification...")
            try:
                final_tables = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)).fetchall()
                final_table_names = [row[0] for row in final_tables]
                logger.info(f"Final tables in database: {final_table_names}")
                
                # Check all required tables
                required_tables = ["videos", "country_relevance", "trending_feeds", "search_cache", "training_labels", "llm_usage_log"]
                missing_tables = [t for t in required_tables if t not in final_table_names]
                
                if not missing_tables:
                    logger.info("✅ All required tables exist successfully!")
                else:
                    logger.error(f"❌ Missing tables after creation: {missing_tables}")
                    
                # Special check for country_relevance table
                if 'country_relevance' in final_table_names:
                    logger.info("✅ country_relevance table verified!")
                else:
                    logger.error("❌ country_relevance table is missing - this will break search functionality!")
                    
            except Exception as e:
                logger.error(f"Final verification failed: {e}")
                
        # If we get here, the transaction was successful
        logger.info("✅ Database table creation transaction completed successfully")
                
    except Exception as e:
        logger.error(f"❌ Database table creation failed: {e}")
        
        # Fallback: Try to create critical tables individually
        logger.info("🔄 Attempting fallback: Creating critical tables individually...")
        try:
            with engine.connect() as fallback_conn:
                # Create the most critical table (country_relevance) first
                critical_tables = [
                    ("videos", """
                        CREATE TABLE IF NOT EXISTS videos (
                            video_id VARCHAR(20) PRIMARY KEY,
                            title TEXT NOT NULL,
                            channel_name VARCHAR(255),
                            channel_country VARCHAR(2),
                            views INTEGER DEFAULT 0,
                            likes INTEGER DEFAULT 0,
                            comments INTEGER DEFAULT 0,
                            upload_date TIMESTAMP WITH TIME ZONE,
                            last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            duration INTEGER,
                            thumbnail_url TEXT,
                            description TEXT,
                            tags JSON
                        );
                    """),
                    ("country_relevance", """
                        CREATE TABLE IF NOT EXISTS country_relevance (
                            video_id VARCHAR(20) NOT NULL,
                            country VARCHAR(2) NOT NULL,
                            relevance_score FLOAT NOT NULL CHECK (relevance_score >= 0.0 AND relevance_score <= 1.0),
                            reasoning TEXT,
                            confidence_score FLOAT CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
                            origin_country VARCHAR(7) DEFAULT 'UNKNOWN',
                            analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            llm_model VARCHAR(50) DEFAULT 'gemini-flash',
                            PRIMARY KEY (video_id, country)
                        );
                    """),
                    ("llm_usage_log", """
                        CREATE TABLE IF NOT EXISTS llm_usage_log (
                            id SERIAL PRIMARY KEY,
                            request_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
                            model_name VARCHAR(50) NOT NULL,
                            input_tokens INTEGER NOT NULL,
                            output_tokens INTEGER NOT NULL,
                            cost_usd NUMERIC(10, 6) NOT NULL,
                            cost_eur NUMERIC(10, 6),
                            exchange_rate NUMERIC(8, 4),
                            country VARCHAR(2),
                            query VARCHAR(255),
                            video_count INTEGER,
                            processing_time_ms INTEGER,
                            cache_hit VARCHAR(10),
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                ]
                
                for table_name, table_sql in critical_tables:
                    try:
                        fallback_conn.execute(text(table_sql))
                        fallback_conn.commit()
                        logger.info(f"✅ Fallback creation successful for {table_name}")
                    except Exception as fallback_error:
                        logger.error(f"❌ Fallback creation failed for {table_name}: {fallback_error}")
                        
        except Exception as fallback_exception:
            logger.error(f"❌ Fallback table creation completely failed: {fallback_exception}")
        
        # Continue startup even if table creation fails (they might already exist)
    
    yield
    
    # Shutdown
    logger.info("Shutting down YouTube Trending Analyzer MVP")


app = FastAPI(
    title="YouTube Trending Analyzer MVP",
    description="""
    🚀 **LLM-powered platform for genuine regional YouTube trend analysis**
    
    ## Features
    - **Multi-country Analysis**: Germany 🇩🇪, USA 🇺🇸, France 🇫🇷, Japan 🇯🇵
    - **LLM-Enhanced Filtering**: Uses Gemini Flash to distinguish real trends from availability
    - **Comprehensive Health Monitoring**: Database, APIs, and system status
    - **Manual Database Setup**: Fallback mechanisms for reliable deployment
    
    ## Quick Start
    1. **Search Trends**: Use `/api/mvp/trending` to find country-specific trending videos
    2. **Health Check**: Use `/api/mvp/health` to monitor system status
    3. **Test APIs**: Use `/api/mvp/test/all` to verify all components
    4. **Database Setup**: Use `/api/mvp/setup/database` if tables need manual creation
    
    ## API Documentation
    - **Interactive Testing**: Use the "Try it out" buttons below to test endpoints
    - **Response Examples**: See real API responses with sample data
    - **Parameter Details**: Understand all query parameters and request formats
    """,
    version="1.1.3-import-fix",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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
    """
    Root endpoint returning API information and interactive documentation links.
    
    **🎯 Quick Access:**
    - **Interactive API Testing**: Visit `/docs` for Swagger UI with "Try it out" buttons
    - **Alternative Documentation**: Visit `/redoc` for ReDoc interface
    - **OpenAPI Schema**: Available at `/openapi.json`
    
    **🔧 Key Endpoints:**
    - **Search**: `/api/mvp/trending?query=gaming&country=DE&timeframe=48h`
    - **Health**: `/api/mvp/health` - System status monitoring
    - **Testing**: `/api/mvp/test/all` - Comprehensive system tests
    - **Database**: `/api/mvp/setup/database` - Manual table creation
    """
    return {
        "message": "🚀 YouTube Trending Analyzer MVP API",
        "version": "1.1.3-import-fix",
        "status": "operational",
        "interactive_docs": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "quick_test_endpoints": [
            "/api/mvp/health",
            "/api/mvp/health/database", 
            "/api/mvp/test/all",
            "/api/mvp/trending?query=gaming&country=DE&timeframe=48h"
        ],
        "build_info": {
            "commit": "import-fix-with-docs",
            "features": [
                "origin_country_detection",
                "multi_tier_search", 
                "search_transparency",
                "batch_llm_processing",
                "adaptive_filtering",
                "interactive_api_docs",
                "comprehensive_health_monitoring"
            ]
        },
        "algorithm": "MVP-LLM-Enhanced",
        "supported_countries": ["DE", "US", "FR", "JP"],
        "supported_timeframes": ["24h", "48h", "7d"]
    }


@app.get("/api/mvp")
async def api_info():
    """
    Detailed API information and endpoint documentation.
    
    **🧪 Interactive Testing Available:**
    - **Swagger UI**: `/docs` - Full interactive API testing interface
    - **ReDoc**: `/redoc` - Clean documentation with examples
    
    **💡 Pro Tip**: Use the Swagger UI `/docs` to test all endpoints with actual parameters!
    """
    return {
        "api_version": "1.1.3-import-fix",
        "build_commit": "import-fix-with-docs",
        "algorithm": "MVP-LLM-Enhanced",
        "llm_provider": "gemini-flash",
        "interactive_testing": {
            "swagger_ui": "/docs",
            "redoc_docs": "/redoc",
            "note": "Use Swagger UI for interactive endpoint testing with 'Try it out' buttons"
        },
        "active_features": {
            "origin_country_detection": True,
            "multi_tier_search": True,
            "search_transparency": True,
            "batch_llm_processing": True,
            "adaptive_filtering": True,
            "cache_invalidation": True,
            "interactive_api_docs": True,
            "comprehensive_testing": True
        },
        "supported_countries": {
            "DE": "Germany 🇩🇪",
            "US": "USA 🇺🇸", 
            "FR": "France 🇫🇷",
            "JP": "Japan 🇯🇵"
        },
        "timeframes": ["24h", "48h", "7d"],
        "key_endpoints": {
            "trending_search": "/api/mvp/trending",
            "health_monitoring": "/api/mvp/health",
            "system_testing": "/api/mvp/test/all",
            "database_setup": "/api/mvp/setup/database",
            "analytics": "/api/mvp/analytics"
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