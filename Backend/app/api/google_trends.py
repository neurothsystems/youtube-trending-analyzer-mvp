from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from app.core.config import validate_country, validate_timeframe, normalize_timeframe, get_country_name
from app.services.google_trends_service import google_trends_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{query}/{country}")
async def get_google_trends(
    query: str,
    country: str,
    timeframe: str = Query("7d", description="Time period: 24h/48h/7d"),
    include_related: bool = Query(False, description="Include related trending queries")
):
    """
    Get Google Trends data for a specific query and country.
    
    **Parameters:**
    - **query**: Search term to analyze
    - **country**: Country code (DE, US, FR, JP)
    - **timeframe**: Time period - 24h, 48h, 7d
    - **include_related**: Whether to include related trending queries
    
    **Returns:**
    - Google Trends score and trending analysis
    - Cross-platform validation data
    - Optional related queries
    """
    try:
        # Validate inputs
        query = query.strip()
        country = country.upper()
        timeframe = normalize_timeframe(timeframe)
        
        if not validate_country(country):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported country code: {country}. Supported: DE, US, FR, JP"
            )
        
        if not validate_timeframe(timeframe):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported timeframe: {timeframe}. Supported: 24h, 48h, 7d"
            )
        
        # Log request
        logger.info(f"Google Trends request: query='{query}', country={country}, timeframe={timeframe}")
        
        # Get Google Trends data
        trends_data = google_trends_service.get_trend_score(query, country, timeframe)
        
        # Get cross-platform validation
        validation_data = google_trends_service.validate_query_trending(
            query, country, youtube_trending=False
        )
        
        # Get related queries if requested
        related_queries = []
        if include_related:
            related_queries = google_trends_service.get_related_queries(query, country)
        
        # Build response
        result = {
            "success": True,
            "query": query,
            "country": country,
            "country_name": get_country_name(country),
            "timeframe": timeframe,
            "google_trends": trends_data,
            "cross_platform_validation": validation_data,
            "related_queries": related_queries if include_related else [],
            "metadata": {
                "service": "Google Trends",
                "cache_hit": trends_data.get('cache_hit', False),
                "data_quality": "high" if trends_data.get('data_points', 0) > 5 else "limited",
                "trending_confidence": validation_data.get('platform_alignment', 'none')
            }
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google Trends error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching Google Trends data")


@router.get("/validation/{query}/{country}")
async def validate_cross_platform_trending(
    query: str,
    country: str,
    youtube_trending: bool = Query(False, description="Whether query is trending on YouTube"),
    timeframe: str = Query("7d", description="Time period for analysis")
):
    """
    Cross-platform validation between Google Trends and YouTube trends.
    
    **Parameters:**
    - **query**: Search term to validate
    - **country**: Country code (DE, US, FR, JP)
    - **youtube_trending**: Whether the query is trending on YouTube
    - **timeframe**: Time period for analysis
    
    **Returns:**
    - Cross-platform validation score
    - Platform alignment assessment
    - Recommendation for trending confidence
    """
    try:
        # Validate inputs
        query = query.strip()
        country = country.upper()
        timeframe = normalize_timeframe(timeframe)
        
        if not validate_country(country):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported country code: {country}. Supported: DE, US, FR, JP"
            )
        
        # Log request
        logger.info(f"Cross-platform validation: query='{query}', country={country}, "
                   f"youtube_trending={youtube_trending}")
        
        # Get validation analysis
        validation_data = google_trends_service.validate_query_trending(
            query, country, youtube_trending
        )
        
        # Get Google Trends data for context
        trends_data = google_trends_service.get_trend_score(query, country, timeframe)
        
        return {
            "success": True,
            "query": query,
            "country": country,
            "country_name": get_country_name(country),
            "validation_result": validation_data,
            "google_trends_context": {
                "trend_score": trends_data.get('trend_score', 0.0),
                "is_trending": trends_data.get('is_trending', False),
                "peak_interest": trends_data.get('peak_interest', 0)
            },
            "recommendation": {
                "confidence_level": validation_data.get('platform_alignment', 'none'),
                "boost_applied": validation_data.get('cross_platform_boost', 0.0),
                "trending_verdict": validation_data.get('recommendation', 'Unknown'),
                "use_for_scoring": validation_data.get('validation_score', 0.0) > 0.3
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cross-platform validation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during validation")


@router.get("/related/{query}/{country}")
async def get_related_trending_queries(
    query: str,
    country: str,
    limit: int = Query(8, description="Maximum number of related queries", ge=1, le=20)
):
    """
    Get related trending queries from Google Trends.
    
    **Parameters:**
    - **query**: Original search term
    - **country**: Country code (DE, US, FR, JP)
    - **limit**: Maximum number of related queries to return
    
    **Returns:**
    - List of related trending queries
    - Potential alternative search terms
    """
    try:
        # Validate inputs
        query = query.strip()
        country = country.upper()
        
        if not validate_country(country):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported country code: {country}. Supported: DE, US, FR, JP"
            )
        
        # Log request
        logger.info(f"Related queries request: query='{query}', country={country}")
        
        # Get related queries
        related_queries = google_trends_service.get_related_queries(query, country)
        
        # Limit results
        limited_queries = related_queries[:limit] if related_queries else []
        
        return {
            "success": True,
            "original_query": query,
            "country": country,
            "country_name": get_country_name(country),
            "related_queries": limited_queries,
            "total_found": len(related_queries),
            "returned": len(limited_queries),
            "suggestion": "Use these queries for expanded search terms or trend validation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Related queries error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching related queries")


@router.get("/status")
async def google_trends_service_status():
    """
    Get Google Trends service status and health check.
    
    **Returns:**
    - Service availability status
    - Rate limiting information
    - Cache performance
    """
    try:
        # Check service availability
        is_available = google_trends_service._is_available()
        
        # Test with a simple query (cached to avoid rate limits)
        test_result = None
        if is_available:
            try:
                test_result = google_trends_service.get_trend_score("test", "US", "7d")
            except Exception as e:
                logger.warning(f"Google Trends test query failed: {e}")
        
        return {
            "success": True,
            "service_status": "operational" if is_available else "unavailable",
            "pytrends_available": is_available,
            "rate_limiting": {
                "active": True,
                "delay_range": "1-3 seconds",
                "recommendation": "Use caching for production"
            },
            "cache_info": {
                "ttl": "2 hours",
                "key_pattern": "google_trends:{country}:{query}:{timeframe}"
            },
            "test_query_status": "success" if test_result and not test_result.get('error') else "failed",
            "dependencies": {
                "pytrends": "4.9.2",
                "redis_cache": "enabled"
            }
        }
        
    except Exception as e:
        logger.error(f"Google Trends status check error: {e}")
        return {
            "success": False,
            "service_status": "error",
            "error": str(e)
        }


@router.get("/enhanced-search/{query}/{country}")
async def get_enhanced_search_terms(
    query: str,
    country: str,
    timeframe: str = Query("7d", description="Time period for analysis")
):
    """
    Get enhanced search terms using Google Trends data.
    
    **NEW FEATURE**: This endpoint demonstrates the revolutionary new search approach
    that combines Google Trends web topics and YouTube search queries instead of
    static LLM-generated search terms.
    
    **Parameters:**
    - **query**: Original search term (e.g. "AI", "gaming", "music")
    - **country**: Country code (DE, US, FR, JP)
    - **timeframe**: Time period (24h, 48h, 7d, 1w)
    
    **Returns:**
    - Enhanced search terms (max 7: 1 original + 1 web topic + 5 YouTube queries)
    - Metadata about the enhancement process
    - Fallback information if Google Trends fails
    
    **Strategy:**
    1. Original query (always included)
    2. Top Related Topic from Google Trends Web Search (cleaned)
    3. Top 5 YouTube Search Queries from Google Trends
    """
    try:
        # Import the search enhancer
        from app.services.google_trends_search_enhancer import google_trends_search_enhancer
        
        # Validate inputs
        if country not in ['DE', 'US', 'FR', 'JP']:
            raise HTTPException(status_code=400, detail="Unsupported country code. Use: DE, US, FR, JP")
        
        if timeframe not in ['24h', '48h', '7d', '1w']:
            raise HTTPException(status_code=400, detail="Unsupported timeframe. Use: 24h, 48h, 7d, 1w")
        
        # Get enhanced search terms with full metadata
        result = google_trends_search_enhancer.get_search_terms_with_metadata(query, country, timeframe)
        
        return {
            "success": True,
            "query": query,
            "country": country,
            "timeframe": timeframe,
            "enhanced_search_terms": result['search_terms'],
            "search_strategy": {
                "source": result['source'],
                "google_trends_available": result['source'] == 'google_trends',
                "web_topic_found": result['web_topic'] is not None,
                "youtube_queries_found": len(result['youtube_queries']),
                "fallback_used": result['source'] == 'fallback'
            },
            "google_trends_data": {
                "web_topic": result['web_topic'],
                "youtube_queries": result['youtube_queries'],
                "cache_hit": result['cache_hit']
            },
            "metadata": {
                "total_terms": len(result['search_terms']),
                "max_terms": 7,
                "strategy": "Original + Web Topic + YouTube Queries",
                "error": result.get('error')
            },
            "usage_note": "These terms will be used in Tier 1 of the MOMENTUM algorithm instead of static country processor terms"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced search terms error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error generating enhanced search terms")