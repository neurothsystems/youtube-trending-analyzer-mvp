from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
from app.core.database import get_db, DatabaseHealthCheck
from app.core.config import settings
from app.services.youtube_service import youtube_service
from app.services.llm_service import llm_service
from app.core.redis import cache

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive system health check.
    
    Checks the status of all critical system components:
    - Database connectivity
    - Redis cache connectivity
    - YouTube API availability
    - LLM service availability
    - Overall system status
    
    **Returns:**
    - Health status for each component
    - Overall system health status
    - Timestamps and basic system info
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "checks": {}
        }
        
        # Database health check
        try:
            db_healthy = DatabaseHealthCheck.check_connection()
            db_info = DatabaseHealthCheck.get_connection_info()
            
            health_status["checks"]["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "connection_pool": db_info,
                "message": "Database connection OK" if db_healthy else "Database connection failed"
            }
            
            if not db_healthy:
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database health check failed"
            }
            health_status["status"] = "degraded"
        
        # Redis cache health check
        try:
            redis_info = cache.get_info()
            cache_healthy = redis_info["status"] == "connected"
            
            health_status["checks"]["redis"] = {
                "status": "healthy" if cache_healthy else "unhealthy",
                "info": redis_info,
                "message": "Redis cache OK" if cache_healthy else "Redis cache connection failed"
            }
            
            if not cache_healthy:
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis health check failed"
            }
            health_status["status"] = "degraded"
        
        # YouTube API health check
        try:
            youtube_healthy = youtube_service._is_available()
            quota_info = youtube_service.get_api_quota_info() if youtube_healthy else {}
            
            health_status["checks"]["youtube_api"] = {
                "status": "healthy" if youtube_healthy else "unhealthy",
                "quota_info": quota_info,
                "message": "YouTube API OK" if youtube_healthy else "YouTube API not available"
            }
            
            if not youtube_healthy:
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["checks"]["youtube_api"] = {
                "status": "unhealthy",
                "error": str(e),
                "message": "YouTube API health check failed"
            }
            health_status["status"] = "degraded"
        
        # LLM service health check
        try:
            llm_healthy = llm_service._is_available()
            cost_info = llm_service.get_cost_info() if llm_healthy else {}
            
            # Check if budget is exceeded
            budget_ok = cost_info.get("budget_used_percentage", 0) < 90
            
            health_status["checks"]["llm_service"] = {
                "status": "healthy" if (llm_healthy and budget_ok) else ("degraded" if llm_healthy else "unhealthy"),
                "cost_info": cost_info,
                "budget_warning": cost_info.get("budget_used_percentage", 0) > 80,
                "message": "LLM service OK" if llm_healthy else "LLM service not available"
            }
            
            if not llm_healthy:
                health_status["status"] = "degraded"
            elif not budget_ok:
                health_status["status"] = "degraded"
                health_status["checks"]["llm_service"]["message"] += " (Budget warning)"
                
        except Exception as e:
            health_status["checks"]["llm_service"] = {
                "status": "unhealthy",
                "error": str(e),
                "message": "LLM service health check failed"
            }
            health_status["status"] = "degraded"
        
        # Overall system assessment
        unhealthy_services = [
            check for check in health_status["checks"].values() 
            if check["status"] == "unhealthy"
        ]
        
        if len(unhealthy_services) >= 2:
            health_status["status"] = "unhealthy"
            health_status["message"] = f"Multiple critical services are down ({len(unhealthy_services)} services)"
        elif health_status["status"] == "degraded":
            degraded_services = [
                service for service, check in health_status["checks"].items()
                if check["status"] in ["unhealthy", "degraded"]
            ]
            health_status["message"] = f"Some services are degraded: {', '.join(degraded_services)}"
        else:
            health_status["message"] = "All systems operational"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Health check system failure",
            "error": str(e)
        }


@router.get("/health/simple")
async def simple_health_check():
    """
    Simple health check endpoint for load balancers.
    
    Returns a minimal health status without detailed checks.
    Useful for quick availability checks by monitoring systems.
    
    **Returns:**
    - Simple OK status or error
    """
    try:
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "YouTube Trending Analyzer MVP"
        }
    except Exception as e:
        logger.error(f"Simple health check error: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes-style readiness probe.
    
    Checks if the service is ready to handle requests.
    This includes checking that all critical dependencies are available.
    
    **Returns:**
    - Ready status if service can handle requests
    - Error if service is not ready
    """
    try:
        # Check critical dependencies
        checks = {
            "database": DatabaseHealthCheck.check_connection(),
            "youtube_api": youtube_service._is_available(),
            "llm_service": llm_service._is_available()
        }
        
        # Service is ready if database and at least one API service is available
        ready = checks["database"] and (checks["youtube_api"] or checks["llm_service"])
        
        if ready:
            return {
                "status": "ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": checks
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "checks": checks,
                    "message": "Service not ready - critical dependencies unavailable"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check error: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "message": "Readiness check failed"
            }
        )


@router.get("/health/database")
async def database_details(db: Session = Depends(get_db)):
    """
    Detailed database health and table information.
    
    Checks database connectivity and lists all tables with their structure.
    Useful for debugging table creation issues.
    
    **Returns:**
    - Database connection status
    - List of existing tables
    - Table creation verification
    """
    try:
        from sqlalchemy import text
        
        # Test basic connection
        db_connected = DatabaseHealthCheck.check_connection()
        
        result = {
            "database_connected": db_connected,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tables": {},
            "required_tables": ["videos", "country_relevance", "trending_feeds", "search_cache", "training_labels"]
        }
        
        if not db_connected:
            result["error"] = "Database connection failed"
            return result
        
        # Get list of all tables
        try:
            tables_query = text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables_result = db.execute(tables_query).fetchall()
            existing_tables = [row[0] for row in tables_result]
            result["existing_tables"] = existing_tables
            
            # Check each required table specifically
            for table_name in result["required_tables"]:
                table_exists = table_name in existing_tables
                result["tables"][table_name] = {
                    "exists": table_exists,
                    "status": "✅ OK" if table_exists else "❌ MISSING"
                }
                
                # If table exists, get column information
                if table_exists:
                    try:
                        columns_query = text(f"""
                            SELECT column_name, data_type, is_nullable, column_default
                            FROM information_schema.columns 
                            WHERE table_name = '{table_name}' AND table_schema = 'public'
                            ORDER BY ordinal_position
                        """)
                        columns_result = db.execute(columns_query).fetchall()
                        result["tables"][table_name]["columns"] = [
                            {
                                "name": row[0],
                                "type": row[1], 
                                "nullable": row[2] == "YES",
                                "default": row[3]
                            } for row in columns_result
                        ]
                        result["tables"][table_name]["column_count"] = len(columns_result)
                    except Exception as col_error:
                        result["tables"][table_name]["column_error"] = str(col_error)
            
            # Overall assessment
            missing_tables = [name for name, info in result["tables"].items() if not info["exists"]]
            result["missing_tables"] = missing_tables
            result["tables_missing_count"] = len(missing_tables)
            result["status"] = "healthy" if len(missing_tables) == 0 else "missing_tables"
            result["message"] = "All required tables exist" if len(missing_tables) == 0 else f"Missing tables: {', '.join(missing_tables)}"
            
        except Exception as e:
            result["error"] = f"Failed to query table information: {str(e)}"
            result["status"] = "error"
            
        return result
        
    except Exception as e:
        logger.error(f"Database details check error: {e}")
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "message": "Database details check failed"
        }


@router.get("/test/youtube")
async def test_youtube_api():
    """
    Test YouTube API functionality with new API key.
    
    Tests basic YouTube API connectivity and quota availability.
    """
    try:
        from app.services.youtube_service import youtube_service
        
        result = {
            "test": "youtube_api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "testing"
        }
        
        # Test 1: API availability
        try:
            is_available = youtube_service._is_available()
            result["api_available"] = is_available
            
            if not is_available:
                result["status"] = "failed"
                result["error"] = "YouTube API not available"
                return result
                
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"YouTube API availability check failed: {str(e)}"
            return result
        
        # Test 2: Simple search test
        try:
            # Test with popular current terms and extend timeframe for testing
            from datetime import datetime, timezone, timedelta
            test_published_after = datetime.now(timezone.utc) - timedelta(days=30)  # 30 days instead of 7
            test_videos = youtube_service.search_videos("gaming", "US", max_results=5, published_after=test_published_after)
            result["search_test"] = {
                "success": True,
                "videos_found": len(test_videos),
                "sample_video_ids": [v['video_id'] for v in test_videos[:3]],
                "test_query": "gaming",
                "test_country": "US",
                "timeframe_days": 30
            }
            
        except Exception as e:
            result["search_test"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 3: Video details test
        if result.get("search_test", {}).get("success") and result["search_test"]["videos_found"] > 0:
            try:
                sample_id = result["search_test"]["sample_video_ids"][0]
                video_details = youtube_service.get_video_details([sample_id])
                result["details_test"] = {
                    "success": True,
                    "video_id": sample_id,
                    "has_title": bool(video_details[0].get('title') if video_details else False),
                    "has_views": bool(video_details[0].get('views') if video_details else False)
                }
                
            except Exception as e:
                result["details_test"] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Test 4: Quota info
        try:
            quota_info = youtube_service.get_api_quota_info()
            result["quota_info"] = quota_info
            
        except Exception as e:
            result["quota_info"] = {"error": str(e)}
        
        # Overall assessment
        search_ok = result.get("search_test", {}).get("success", False)
        details_ok = result.get("details_test", {}).get("success", True)  # Optional
        
        if search_ok:
            result["status"] = "passed"
            result["message"] = "YouTube API is working correctly"
        else:
            result["status"] = "failed"
            result["message"] = "YouTube API has issues"
            
        return result
        
    except Exception as e:
        logger.error(f"YouTube API test error: {e}")
        return {
            "test": "youtube_api",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "message": "YouTube API test system failure"
        }


@router.get("/test/gemini")
async def test_gemini_api():
    """
    Test Gemini LLM API functionality with new API key.
    
    Tests basic Gemini API connectivity and simple analysis.
    """
    try:
        from app.services.llm_service import llm_service
        
        result = {
            "test": "gemini_api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "testing"
        }
        
        # Test 1: API availability
        try:
            is_available = llm_service._is_available()
            result["api_available"] = is_available
            
            if not is_available:
                result["status"] = "failed"
                result["error"] = "Gemini API not available"
                return result
                
        except Exception as e:
            result["status"] = "failed"
            result["error"] = f"Gemini API availability check failed: {str(e)}"
            return result
        
        # Test 2: Simple text analysis
        try:
            # Create a simple test video object
            class TestVideo:
                def __init__(self):
                    self.video_id = "test123"
                    self.title = "German Gaming Tutorial - Minecraft Survival Guide"
                    self.channel_name = "DeutscherGamer"
                    self.description = "Ein ausführlicher Guide zum Überleben in Minecraft auf Deutsch"
                    self.tags = ["minecraft", "gaming", "deutsch", "tutorial"]
                    
            test_video = TestVideo()
            
            # Test country relevance analysis for Germany
            analysis_result = llm_service.analyze_country_relevance_batch(
                [test_video], "DE"
            )
            
            result["analysis_test"] = {
                "success": True,
                "video_analyzed": test_video.video_id,
                "relevance_score": analysis_result[0].relevance_score if analysis_result else None,
                "reasoning_provided": bool(analysis_result[0].reasoning if analysis_result else False),
                "origin_country": analysis_result[0].origin_country if analysis_result else None
            }
            
        except Exception as e:
            result["analysis_test"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test 3: Cost tracking
        try:
            cost_info = llm_service.get_cost_info()
            result["cost_info"] = cost_info
            
        except Exception as e:
            result["cost_info"] = {"error": str(e)}
        
        # Test 4: Search term expansion
        try:
            expanded_terms = llm_service.expand_search_terms("gaming", "DE")
            result["expansion_test"] = {
                "success": True,
                "original_term": "gaming",
                "country": "DE",
                "expanded_terms": expanded_terms[:5] if expanded_terms else []
            }
            
        except Exception as e:
            result["expansion_test"] = {
                "success": False,
                "error": str(e)
            }
        
        # Overall assessment
        analysis_ok = result.get("analysis_test", {}).get("success", False)
        expansion_ok = result.get("expansion_test", {}).get("success", True)  # Optional
        
        if analysis_ok:
            result["status"] = "passed"
            result["message"] = "Gemini API is working correctly"
        else:
            result["status"] = "failed" 
            result["message"] = "Gemini API has issues"
            
        return result
        
    except Exception as e:
        logger.error(f"Gemini API test error: {e}")
        return {
            "test": "gemini_api",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "message": "Gemini API test system failure"
        }


@router.get("/test/database")
async def test_database_operations(db: Session = Depends(get_db)):
    """
    Test database operations and table functionality.
    
    Tests table creation, insertion, querying, and cleanup.
    """
    try:
        from sqlalchemy import text
        from app.models.video import Video
        from app.models.country_relevance import CountryRelevance
        import uuid
        from datetime import datetime, timezone
        
        result = {
            "test": "database_operations",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "testing",
            "operations": {}
        }
        
        # Test 1: Basic connection
        try:
            db.execute(text("SELECT 1"))
            result["operations"]["connection"] = {"success": True, "message": "Database connection OK"}
        except Exception as e:
            result["operations"]["connection"] = {"success": False, "error": str(e)}
            result["status"] = "failed"
            return result
        
        # Test 2: Table existence check
        try:
            tables_query = text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tables_result = db.execute(tables_query).fetchall()
            existing_tables = [row[0] for row in tables_result]
            
            required_tables = ["videos", "country_relevance", "trending_feeds", "search_cache", "training_labels"]
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            result["operations"]["tables_check"] = {
                "success": len(missing_tables) == 0,
                "existing_tables": existing_tables,
                "missing_tables": missing_tables,
                "message": "All tables exist" if len(missing_tables) == 0 else f"Missing: {missing_tables}"
            }
            
            if missing_tables:
                result["status"] = "failed"
                return result
                
        except Exception as e:
            result["operations"]["tables_check"] = {"success": False, "error": str(e)}
            result["status"] = "failed"
            return result
        
        # Test 3: Insert test video
        test_video_id = f"test_{uuid.uuid4().hex[:8]}"
        try:
            test_video = Video(
                video_id=test_video_id,
                title="Test Video for Database",
                channel_name="Test Channel",
                channel_country="US",
                views=1000,
                likes=50,
                comments=10,
                duration=120
            )
            db.add(test_video)
            db.commit()
            
            result["operations"]["video_insert"] = {
                "success": True,
                "test_video_id": test_video_id,
                "message": "Test video inserted successfully"
            }
            
        except Exception as e:
            result["operations"]["video_insert"] = {"success": False, "error": str(e)}
            db.rollback()
            result["status"] = "failed"
            return result
        
        # Test 4: Insert country relevance
        try:
            test_relevance = CountryRelevance(
                video_id=test_video_id,
                country="US",
                relevance_score=0.85,
                reasoning="Test relevance analysis",
                confidence_score=0.9,
                origin_country="US",
                llm_model="gemini-flash"
            )
            db.add(test_relevance)
            db.commit()
            
            result["operations"]["relevance_insert"] = {
                "success": True,
                "message": "Country relevance inserted successfully"
            }
            
        except Exception as e:
            result["operations"]["relevance_insert"] = {"success": False, "error": str(e)}
            db.rollback()
        
        # Test 5: Query test
        try:
            query_result = db.query(CountryRelevance).filter(
                CountryRelevance.video_id == test_video_id
            ).first()
            
            result["operations"]["query_test"] = {
                "success": query_result is not None,
                "relevance_score": query_result.relevance_score if query_result else None,
                "message": "Query successful" if query_result else "Query returned no results"
            }
            
        except Exception as e:
            result["operations"]["query_test"] = {"success": False, "error": str(e)}
        
        # Test 6: Cleanup test data
        try:
            db.query(CountryRelevance).filter(CountryRelevance.video_id == test_video_id).delete()
            db.query(Video).filter(Video.video_id == test_video_id).delete()
            db.commit()
            
            result["operations"]["cleanup"] = {
                "success": True,
                "message": "Test data cleaned up successfully"
            }
            
        except Exception as e:
            result["operations"]["cleanup"] = {"success": False, "error": str(e)}
            db.rollback()
        
        # Overall assessment
        critical_ops = ["connection", "tables_check", "video_insert", "relevance_insert", "query_test"]
        failed_ops = [op for op in critical_ops if not result["operations"].get(op, {}).get("success", False)]
        
        if not failed_ops:
            result["status"] = "passed"
            result["message"] = "All database operations working correctly"
        else:
            result["status"] = "failed"
            result["message"] = f"Failed operations: {failed_ops}"
            
        return result
        
    except Exception as e:
        logger.error(f"Database test error: {e}")
        return {
            "test": "database_operations",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "message": "Database test system failure"
        }


@router.get("/test/all")
async def test_all_systems(db: Session = Depends(get_db)):
    """
    Run all system tests in sequence.
    
    Tests YouTube API, Gemini API, and database operations.
    """
    try:
        result = {
            "test": "all_systems",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "testing",
            "tests": {}
        }
        
        # Run individual tests
        youtube_result = await test_youtube_api()
        result["tests"]["youtube"] = youtube_result
        
        gemini_result = await test_gemini_api()
        result["tests"]["gemini"] = gemini_result
        
        database_result = await test_database_operations(db)
        result["tests"]["database"] = database_result
        
        # Overall assessment
        test_results = [
            result["tests"]["youtube"]["status"],
            result["tests"]["gemini"]["status"], 
            result["tests"]["database"]["status"]
        ]
        
        passed_tests = test_results.count("passed")
        failed_tests = test_results.count("failed")
        error_tests = test_results.count("error")
        
        if failed_tests == 0 and error_tests == 0:
            result["status"] = "passed"
            result["message"] = "All systems operational"
        elif failed_tests > 0:
            result["status"] = "failed"
            result["message"] = f"{failed_tests} system(s) failed, {passed_tests} passed"
        else:
            result["status"] = "error"
            result["message"] = f"{error_tests} system(s) had errors, {passed_tests} passed"
        
        result["summary"] = {
            "total_tests": 3,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests
        }
        
        return result
        
    except Exception as e:
        logger.error(f"All systems test error: {e}")
        return {
            "test": "all_systems",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "message": "System test failure"
        }


@router.post("/setup/database")
async def setup_database(db: Session = Depends(get_db)):
    """
    Manual database setup endpoint.
    
    Creates all required database tables manually. This can be used
    if the automatic startup initialization fails.
    
    **Returns:**
    - Setup status and details
    """
    try:
        from sqlalchemy import text
        
        result = {
            "setup": "database_tables",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "starting",
            "operations": []
        }
        
        # Manual table creation SQL
        tables_sql = {
            "videos": """
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
            "country_relevance": """
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
            "trending_feeds": """
                CREATE TABLE IF NOT EXISTS trending_feeds (
                    id SERIAL PRIMARY KEY,
                    video_id VARCHAR(20) NOT NULL,
                    country VARCHAR(2) NOT NULL,
                    trending_rank INTEGER,
                    category VARCHAR(50),
                    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """,
            "search_cache": """
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
            "training_labels": """
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
            """
        }
        
        # Create tables one by one
        for table_name, table_sql in tables_sql.items():
            try:
                db.execute(text(table_sql))
                db.commit()
                result["operations"].append({
                    "table": table_name,
                    "status": "created",
                    "message": f"Table {table_name} created successfully"
                })
            except Exception as e:
                result["operations"].append({
                    "table": table_name,
                    "status": "error",
                    "error": str(e),
                    "message": f"Failed to create table {table_name}"
                })
        
        # Create basic indexes
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_upload_date ON videos (upload_date);",
            "CREATE INDEX IF NOT EXISTS idx_views ON videos (views);",
            "CREATE INDEX IF NOT EXISTS idx_country_score ON country_relevance (country, relevance_score);",
            "CREATE INDEX IF NOT EXISTS idx_video_country ON country_relevance (video_id, country);",
            "CREATE INDEX IF NOT EXISTS idx_country_captured ON trending_feeds (country, captured_at);",
            "CREATE INDEX IF NOT EXISTS idx_expires ON search_cache (expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_training_country ON training_labels (country);"
        ]
        
        indexes_created = 0
        for index_sql in indexes_sql:
            try:
                db.execute(text(index_sql))
                db.commit()
                indexes_created += 1
            except Exception as e:
                # Non-critical - continue with other indexes
                pass
        
        result["indexes_created"] = indexes_created
        result["total_indexes"] = len(indexes_sql)
        
        # Final verification
        verification_query = text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        tables_result = db.execute(verification_query).fetchall()
        created_tables = [row[0] for row in tables_result]
        
        result["created_tables"] = created_tables
        result["missing_tables"] = [t for t in tables_sql.keys() if t not in created_tables]
        
        if not result["missing_tables"]:
            result["status"] = "success"
            result["message"] = "All database tables created successfully"
        else:
            result["status"] = "partial"
            result["message"] = f"Some tables missing: {result['missing_tables']}"
            
        return result
        
    except Exception as e:
        logger.error(f"Database setup error: {e}")
        return {
            "setup": "database_tables",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "message": "Database setup failed"
        }


@router.get("/debug/youtube-search")
async def debug_youtube_search():
    """
    Debug YouTube search with different parameter combinations.
    
    Tests various search configurations to identify why searches return 0 results.
    """
    try:
        from app.services.youtube_service import youtube_service
        from datetime import datetime, timezone, timedelta
        
        if not youtube_service._is_available():
            return {"error": "YouTube API not available"}
        
        results = {
            "debug": "youtube_search_configurations",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tests": {}
        }
        
        # Test parameters
        test_query = "gaming"
        test_country = "DE"
        published_after = datetime.now(timezone.utc) - timedelta(days=30)
        published_after_str = published_after.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Test 1: Minimal search (no filters)
        try:
            request1 = youtube_service.youtube.search().list(
                part='id,snippet',
                q=test_query,
                type='video',
                maxResults=5
            )
            response1 = request1.execute()
            results["tests"]["minimal_search"] = {
                "config": "q, type=video only",
                "videos_found": len(response1.get('items', [])),
                "success": True
            }
        except Exception as e:
            results["tests"]["minimal_search"] = {
                "config": "q, type=video only",
                "success": False,
                "error": str(e)
            }
        
        # Test 2: With region code
        try:
            request2 = youtube_service.youtube.search().list(
                part='id,snippet',
                q=test_query,
                type='video',
                regionCode=test_country,
                maxResults=5
            )
            response2 = request2.execute()
            results["tests"]["with_region"] = {
                "config": "q, type=video, regionCode=DE",
                "videos_found": len(response2.get('items', [])),
                "success": True
            }
        except Exception as e:
            results["tests"]["with_region"] = {
                "config": "q, type=video, regionCode=DE",
                "success": False,
                "error": str(e)
            }
        
        # Test 3: With time restriction
        try:
            request3 = youtube_service.youtube.search().list(
                part='id,snippet',
                q=test_query,
                type='video',
                publishedAfter=published_after_str,
                maxResults=5
            )
            response3 = request3.execute()
            results["tests"]["with_time"] = {
                "config": f"q, type=video, publishedAfter={published_after_str}",
                "videos_found": len(response3.get('items', [])),
                "success": True
            }
        except Exception as e:
            results["tests"]["with_time"] = {
                "config": f"q, type=video, publishedAfter={published_after_str}",
                "success": False,
                "error": str(e)
            }
        
        # Test 4: Full current configuration
        try:
            request4 = youtube_service.youtube.search().list(
                part='id,snippet',
                q=test_query,
                type='video',
                regionCode=test_country,
                maxResults=5,
                publishedAfter=published_after_str,
                order='relevance',
                videoDuration='any',
                videoEmbeddable='true'
            )
            response4 = request4.execute()
            results["tests"]["full_config"] = {
                "config": "All current filters (regionCode, publishedAfter, videoEmbeddable=true)",
                "videos_found": len(response4.get('items', [])),
                "success": True
            }
        except Exception as e:
            results["tests"]["full_config"] = {
                "config": "All current filters",
                "success": False,
                "error": str(e)
            }
        
        # Test 5: Without videoEmbeddable
        try:
            request5 = youtube_service.youtube.search().list(
                part='id,snippet',
                q=test_query,
                type='video',
                regionCode=test_country,
                maxResults=5,
                publishedAfter=published_after_str,
                order='relevance'
            )
            response5 = request5.execute()
            results["tests"]["no_embeddable"] = {
                "config": "No videoEmbeddable filter",
                "videos_found": len(response5.get('items', [])),
                "success": True
            }
        except Exception as e:
            results["tests"]["no_embeddable"] = {
                "config": "No videoEmbeddable filter",
                "success": False,
                "error": str(e)
            }
        
        # Summary
        successful_tests = [name for name, test in results["tests"].items() if test.get("success")]
        results["summary"] = {
            "total_tests": len(results["tests"]),
            "successful_tests": len(successful_tests),
            "failed_tests": len(results["tests"]) - len(successful_tests),
            "recommendation": "Check which configuration returns the most videos"
        }
        
        return results
        
    except Exception as e:
        logger.error(f"YouTube search debug error: {e}")
        return {
            "debug": "youtube_search_configurations",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


@router.get("/debug/trending-service")
async def debug_trending_service(db: Session = Depends(get_db)):
    """
    Debug the trending service step by step to identify where it fails.
    """
    try:
        from app.services.trending_service import trending_service
        from app.services.country_processors import CountryProcessorFactory
        from app.core.config import get_timeframe_hours
        from datetime import datetime, timezone, timedelta
        
        result = {
            "debug": "trending_service_step_by_step",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_params": {
                "query": "gaming",
                "country": "DE", 
                "timeframe": "48h"
            },
            "steps": {}
        }
        
        query = "gaming"
        country = "DE"
        timeframe = "48h"
        
        # Step 1: Test country processor
        try:
            processor = CountryProcessorFactory.get_processor(country)
            timeframe_hours = get_timeframe_hours(timeframe)
            published_after = datetime.now(timezone.utc) - timedelta(hours=timeframe_hours)
            
            # Get search terms
            tier_1_terms = processor.get_local_search_terms(query)[:5]
            tier_2_terms = processor.get_category_terms(query)[:3] 
            tier_3_terms = processor.get_generic_trending_terms()[:2]
            
            result["steps"]["country_processor"] = {
                "success": True,
                "processor_type": type(processor).__name__,
                "timeframe_hours": timeframe_hours,
                "published_after": published_after.isoformat(),
                "search_terms": {
                    "tier_1": tier_1_terms,
                    "tier_2": tier_2_terms,
                    "tier_3": tier_3_terms,
                    "total_terms": len(tier_1_terms) + len(tier_2_terms) + len(tier_3_terms)
                }
            }
        except Exception as e:
            result["steps"]["country_processor"] = {
                "success": False,
                "error": str(e)
            }
            return result
        
        # Step 2: Test individual search terms
        try:
            from app.services.youtube_service import youtube_service
            search_results = {}
            total_videos = 0
            
            # Test each tier of terms
            for tier_name, terms in [("tier_1", tier_1_terms), ("tier_2", tier_2_terms), ("tier_3", tier_3_terms)]:
                tier_results = {}
                for term in terms[:2]:  # Only test first 2 terms per tier to save quota
                    videos = youtube_service.search_videos(
                        term, 
                        country,
                        max_results=10,
                        published_after=published_after
                    )
                    tier_results[term] = len(videos)
                    total_videos += len(videos)
                search_results[tier_name] = tier_results
            
            result["steps"]["search_terms_test"] = {
                "success": True,
                "results_per_term": search_results,
                "total_videos_found": total_videos
            }
        except Exception as e:
            result["steps"]["search_terms_test"] = {
                "success": False,
                "error": str(e)
            }
            return result
        
        # Step 3: Test trending service collection method directly
        try:
            # Test the private _collect_videos method if possible
            videos, transparency_data = trending_service._collect_videos(query, country, timeframe, db)
            
            result["steps"]["collect_videos"] = {
                "success": True,
                "videos_collected": len(videos),
                "transparency_data": transparency_data
            }
        except Exception as e:
            result["steps"]["collect_videos"] = {
                "success": False,
                "error": str(e)
            }
        
        # Step 4: Test full trending analysis
        try:
            trending_result = trending_service.analyze_trending_videos(query, country, timeframe, db, limit=10)
            
            result["steps"]["full_analysis"] = {
                "success": trending_result.get("success", False),
                "results_count": len(trending_result.get("results", [])),
                "metadata": trending_result.get("metadata", {}),
                "message": trending_result.get("metadata", {}).get("message", "No message")
            }
        except Exception as e:
            result["steps"]["full_analysis"] = {
                "success": False,
                "error": str(e)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Trending service debug error: {e}")
        return {
            "debug": "trending_service_step_by_step",
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe.
    
    Checks if the service process is alive and responsive.
    This is a minimal check that should always succeed if the process is running.
    
    **Returns:**
    - Alive status if the service process is responsive
    """
    try:
        return {
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pid": "N/A",  # Could add actual PID if needed
            "uptime_seconds": "N/A"  # Could add actual uptime if needed
        }
    except Exception as e:
        logger.error(f"Liveness check error: {e}")
        # Even if there's an error, return 200 if the process is responsive enough to handle this
        return {
            "status": "alive_with_errors",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }