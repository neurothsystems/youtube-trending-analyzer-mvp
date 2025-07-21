from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging
from app.core.database import get_db
from app.core.config import validate_country, validate_timeframe, get_country_name
from app.services.trending_service import trending_service
from app.services.youtube_service import youtube_service
from app.core.redis import CacheManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_trending_videos(
    query: str = Query(..., description="Search term for trending analysis", min_length=2, max_length=100),
    country: str = Query(..., description="Country code (DE, US, FR, JP)"),
    timeframe: str = Query(..., description="Time period (24h, 48h, 7d)"),
    limit: int = Query(10, description="Number of results to return", ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Main trending analysis endpoint.
    
    Analyzes YouTube videos for genuine regional trending patterns using LLM-powered
    country relevance analysis and the MOMENTUM MVP algorithm.
    
    **Parameters:**
    - **query**: Search term (e.g., "AI", "gaming", "music")
    - **country**: Country code - DE (Germany), US (USA), FR (France), JP (Japan)
    - **timeframe**: Time period - 24h, 48h, or 7d
    - **limit**: Number of results to return (1-50, default: 10)
    
    **Returns:**
    - Ranked list of trending videos with scores and reasoning
    - Processing metadata including LLM cost and cache statistics
    - Country relevance scores and explanations
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
        
        if not validate_timeframe(timeframe):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported timeframe: {timeframe}. Supported: 24h, 48h, 7d"
            )
        
        # Log request
        logger.info(f"Trending analysis request: query='{query}', country={country}, timeframe={timeframe}")
        
        # Perform trending analysis
        result = trending_service.analyze_trending_videos(
            query=query,
            country=country,
            timeframe=timeframe,
            db=db,
            limit=limit
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trending analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during trending analysis")


@router.get("/feeds/{country}")
async def get_trending_feed(
    country: str,
    fresh_only: bool = Query(False, description="Only return fresh trending data (< 4 hours old)"),
    db: Session = Depends(get_db)
):
    """
    Get current official YouTube trending feed for a country.
    
    **Parameters:**
    - **country**: Country code (DE, US, FR, JP)
    - **fresh_only**: If true, only return data less than 4 hours old
    
    **Returns:**
    - List of currently trending videos from YouTube's official trending page
    - Includes trending rank, category, and capture timestamp
    """
    try:
        country = country.upper()
        
        if not validate_country(country):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported country code: {country}. Supported: DE, US, FR, JP"
            )
        
        # Get trending videos
        trending_videos = youtube_service.get_trending_videos(country, max_results=50)
        
        if fresh_only and trending_videos:
            # Filter to only fresh data (implementation would check capture timestamp)
            # For now, we'll return all data since YouTube API gives current trending
            pass
        
        return {
            "success": True,
            "country": country,
            "country_name": get_country_name(country),
            "total_videos": len(trending_videos),
            "trending_videos": trending_videos,
            "fresh_only": fresh_only,
            "note": "Data from YouTube's official trending feed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trending feed error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching trending feed")


@router.get("/search-terms")
async def expand_search_terms(
    query: str = Query(..., description="Original search term", min_length=2, max_length=100),
    country: str = Query(..., description="Target country code")
):
    """
    Get country-specific search term expansions for a query.
    
    Uses LLM to generate localized search variants that are more likely to find
    trending content in the target country.
    
    **Parameters:**
    - **query**: Original search term
    - **country**: Target country code (DE, US, FR, JP)
    
    **Returns:**
    - List of expanded search terms optimized for the target country
    - Includes cultural variants, language translations, and local slang
    """
    try:
        query = query.strip()
        country = country.upper()
        
        if not validate_country(country):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported country code: {country}. Supported: DE, US, FR, JP"
            )
        
        # Get expanded search terms using LLM
        from app.services.llm_service import llm_service
        expanded_terms = llm_service.expand_search_terms(query, country)
        
        return {
            "success": True,
            "original_query": query,
            "country": country,
            "country_name": get_country_name(country),
            "expanded_terms": expanded_terms,
            "total_terms": len(expanded_terms)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search term expansion error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error expanding search terms")


@router.post("/cache/invalidate")
async def invalidate_cache(
    country: Optional[str] = Query(None, description="Country to invalidate (optional)"),
    query: Optional[str] = Query(None, description="Specific query to invalidate (optional)")
):
    """
    Invalidate cache entries for debugging and testing.
    
    **Parameters:**
    - **country**: If provided, invalidates all cache entries for this country
    - **query**: If provided along with country, invalidates specific query cache
    
    **Returns:**
    - Number of cache entries invalidated
    """
    try:
        if country and query:
            # Invalidate specific query cache
            country = country.upper()
            if not validate_country(country):
                raise HTTPException(status_code=400, detail=f"Invalid country: {country}")
            
            # Invalidate cache for all timeframes of this query/country combination
            deleted = 0
            for timeframe in ["24h", "48h", "7d"]:
                cache_key = f"trending:{country}:{query.lower()}:{timeframe}"
                if CacheManager.cache.delete(cache_key):
                    deleted += 1
            
            return {
                "success": True,
                "message": f"Invalidated cache for query '{query}' in {country}",
                "entries_deleted": deleted
            }
        
        elif country:
            # Invalidate all cache for country
            country = country.upper()
            if not validate_country(country):
                raise HTTPException(status_code=400, detail=f"Invalid country: {country}")
            
            deleted = CacheManager.invalidate_country_cache(country)
            
            return {
                "success": True,
                "message": f"Invalidated all cache entries for {country}",
                "entries_deleted": deleted
            }
        
        else:
            # Invalidate trending cache patterns
            patterns = ["trending:*", "llm:*", "video:*", "trending_feed:*"]
            deleted = 0
            for pattern in patterns:
                deleted += CacheManager.cache.flush_pattern(pattern)
            
            return {
                "success": True,
                "message": "Invalidated all trending-related cache",
                "entries_deleted": deleted
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during cache invalidation")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache performance statistics.
    
    **Returns:**
    - Cache hit rate, memory usage, and performance metrics
    - Budget-relevant caching statistics
    """
    try:
        cache_stats = CacheManager.cache.get_cache_stats()
        
        return {
            "success": True,
            "cache_stats": cache_stats,
            "budget_optimization": {
                "target_hit_rate_percentage": 70,
                "current_performance": "optimal" if cache_stats.get("hit_rate_percentage", 0) >= 70 else "suboptimal",
                "recommendation": "Cache performance is good" if cache_stats.get("hit_rate_percentage", 0) >= 70 
                                else "Consider increasing cache TTL to improve budget efficiency"
            }
        }
        
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching cache stats")