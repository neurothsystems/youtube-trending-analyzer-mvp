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