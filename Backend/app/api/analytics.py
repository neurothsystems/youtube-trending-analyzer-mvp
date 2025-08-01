from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging
from app.core.database import get_db
from app.core.config import validate_country, get_country_name, settings
from app.models.video import Video
from app.models.country_relevance import CountryRelevance
from app.models.trending_feed import TrendingFeed
from app.models.search_cache import SearchCache
from app.services.llm_service import llm_service
from app.core.redis import cache

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/country/{country}")
async def get_country_analytics(
    country: str,
    days: int = Query(7, description="Number of days to analyze", ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for a specific country.
    
    **Parameters:**
    - **country**: Country code (DE, US, FR, JP)
    - **days**: Number of days to analyze (1-30, default: 7)
    
    **Returns:**
    - Country-specific trending statistics
    - LLM analysis performance metrics
    - Popular queries and content patterns
    - Trending feed analysis
    """
    try:
        country = country.upper()
        
        if not validate_country(country):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported country code: {country}. Supported: DE, US, FR, JP"
            )
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Video statistics
        total_videos_analyzed = db.query(CountryRelevance).filter(
            CountryRelevance.country == country,
            CountryRelevance.analyzed_at >= start_date
        ).count()
        
        # Average relevance score
        avg_relevance = db.query(func.avg(CountryRelevance.relevance_score)).filter(
            CountryRelevance.country == country,
            CountryRelevance.analyzed_at >= start_date
        ).scalar() or 0.0
        
        # High relevance videos (>= 0.8)
        high_relevance_count = db.query(CountryRelevance).filter(
            CountryRelevance.country == country,
            CountryRelevance.relevance_score >= 0.8,
            CountryRelevance.analyzed_at >= start_date
        ).count()
        
        # Trending feed statistics
        trending_feed_count = db.query(TrendingFeed).filter(
            TrendingFeed.country == country,
            TrendingFeed.captured_at >= start_date
        ).count()
        
        # Get trending feed matches (videos that appear in both our analysis and trending feed)
        trending_matches = db.query(CountryRelevance).join(
            TrendingFeed, 
            (CountryRelevance.video_id == TrendingFeed.video_id) &
            (CountryRelevance.country == TrendingFeed.country)
        ).filter(
            CountryRelevance.country == country,
            CountryRelevance.analyzed_at >= start_date,
            TrendingFeed.captured_at >= start_date
        ).count()
        
        # Popular search queries
        popular_queries = db.query(
            SearchCache.query,
            func.count(SearchCache.query).label('search_count')
        ).filter(
            SearchCache.country == country,
            SearchCache.created_at >= start_date
        ).group_by(SearchCache.query).order_by(desc('search_count')).limit(10).all()
        
        # Top performing videos by relevance score
        top_videos = db.query(
            CountryRelevance,
            Video.title,
            Video.channel_name,
            Video.views
        ).join(Video).filter(
            CountryRelevance.country == country,
            CountryRelevance.analyzed_at >= start_date
        ).order_by(desc(CountryRelevance.relevance_score)).limit(10).all()
        
        # Format top videos
        formatted_top_videos = []
        for relevance, title, channel_name, views in top_videos:
            formatted_top_videos.append({
                'video_id': relevance.video_id,
                'title': title,
                'channel_name': channel_name,
                'relevance_score': round(relevance.relevance_score, 3),
                'reasoning': relevance.reasoning,
                'views': views,
                'analyzed_at': relevance.analyzed_at.isoformat()
            })
        
        # LLM performance metrics
        confidence_avg = db.query(func.avg(CountryRelevance.confidence_score)).filter(
            CountryRelevance.country == country,
            CountryRelevance.analyzed_at >= start_date
        ).scalar() or 0.0
        
        return {
            "success": True,
            "country": country,
            "country_name": get_country_name(country),
            "analysis_period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "video_statistics": {
                "total_videos_analyzed": total_videos_analyzed,
                "average_relevance_score": round(avg_relevance, 3),
                "high_relevance_count": high_relevance_count,
                "high_relevance_percentage": round((high_relevance_count / max(total_videos_analyzed, 1)) * 100, 1)
            },
            "trending_feed_statistics": {
                "trending_feed_entries": trending_feed_count,
                "trending_matches": trending_matches,
                "match_rate_percentage": round((trending_matches / max(trending_feed_count, 1)) * 100, 1)
            },
            "llm_performance": {
                "average_confidence_score": round(confidence_avg, 3),
                "model_used": "gemini-flash"
            },
            "popular_queries": [
                {"query": query, "search_count": count} 
                for query, count in popular_queries
            ],
            "top_videos": formatted_top_videos
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Country analytics error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching country analytics")


@router.get("/system")
async def get_system_analytics(
    days: int = Query(7, description="Number of days to analyze", ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get system-wide analytics and performance metrics.
    
    **Parameters:**
    - **days**: Number of days to analyze (1-30, default: 7)
    
    **Returns:**
    - Overall system performance metrics
    - API usage statistics
    - Cache performance data
    - LLM cost and usage tracking
    - Database statistics
    """
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # System metrics
        total_searches = db.query(SearchCache).filter(
            SearchCache.created_at >= start_date
        ).count()
        
        # Unique queries
        unique_queries = db.query(func.count(func.distinct(SearchCache.query))).filter(
            SearchCache.created_at >= start_date
        ).scalar() or 0
        
        # Cache performance
        cache_stats = cache.get_cache_stats()
        
        # LLM cost information
        llm_cost_info = llm_service.get_cost_info() if llm_service._is_available() else {}
        
        # Database statistics
        total_videos = db.query(Video).count()
        total_country_analysis = db.query(CountryRelevance).count()
        total_trending_entries = db.query(TrendingFeed).count()
        
        # Recent activity
        recent_videos = db.query(Video).filter(
            Video.last_updated >= start_date
        ).count()
        
        recent_analysis = db.query(CountryRelevance).filter(
            CountryRelevance.analyzed_at >= start_date
        ).count()
        
        # Country distribution
        country_stats = db.query(
            CountryRelevance.country,
            func.count(CountryRelevance.video_id).label('analysis_count'),
            func.avg(CountryRelevance.relevance_score).label('avg_score')
        ).filter(
            CountryRelevance.analyzed_at >= start_date
        ).group_by(CountryRelevance.country).all()
        
        formatted_country_stats = []
        for country, analysis_count, avg_score in country_stats:
            formatted_country_stats.append({
                'country': country,
                'country_name': get_country_name(country),
                'analysis_count': analysis_count,
                'average_relevance_score': round(float(avg_score) if avg_score else 0.0, 3)
            })
        
        return {
            "success": True,
            "system_info": {
                "service_name": "YouTube Trending Analyzer MVP",
                "version": settings.VERSION,
                "algorithm": "MVP-LLM-Enhanced",
                "environment": settings.ENVIRONMENT
            },
            "analysis_period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "api_usage": {
                "total_searches": total_searches,
                "unique_queries": unique_queries,
                "searches_per_day": round(total_searches / max(days, 1), 1)
            },
            "cache_performance": cache_stats,
            "llm_usage": llm_cost_info,
            "database_statistics": {
                "total_videos": total_videos,
                "total_country_analyses": total_country_analysis,
                "total_trending_entries": total_trending_entries,
                "recent_videos_added": recent_videos,
                "recent_analyses_performed": recent_analysis
            },
            "country_statistics": formatted_country_stats,
            "performance_targets": {
                "response_time_target_ms": settings.MAX_RESPONSE_TIME * 1000,
                "cache_hit_rate_target": settings.TARGET_CACHE_HIT_RATE * 100,
                "monthly_budget_eur": settings.LLM_MONTHLY_BUDGET
            }
        }
        
    except Exception as e:
        logger.error(f"System analytics error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching system analytics")


@router.get("/budget")
async def get_budget_analytics():
    """
    Get detailed budget and cost analytics.
    
    Provides comprehensive information about LLM usage costs, API quotas,
    and budget optimization metrics.
    
    **Returns:**
    - Current LLM cost breakdown
    - Budget utilization and remaining budget
    - Cost optimization recommendations
    - API quota usage estimates
    """
    try:
        # LLM cost information
        llm_cost_info = llm_service.get_cost_info() if llm_service._is_available() else {
            "daily_cost_eur": 0.0,
            "monthly_cost_eur": 0.0,
            "monthly_budget_eur": settings.LLM_MONTHLY_BUDGET,
            "budget_remaining_eur": settings.LLM_MONTHLY_BUDGET,
            "budget_used_percentage": 0.0
        }
        
        # Cache performance for budget optimization
        cache_stats = cache.get_cache_stats()
        cache_hit_rate = cache_stats.get("hit_rate_percentage", 0)
        
        # Budget status assessment
        budget_used_pct = llm_cost_info.get("budget_used_percentage", 0)
        
        if budget_used_pct >= 90:
            budget_status = "critical"
            budget_message = "Budget nearly exhausted - implement cost controls immediately"
        elif budget_used_pct >= 80:
            budget_status = "warning"
            budget_message = "Budget usage high - monitor closely and optimize caching"
        elif budget_used_pct >= 60:
            budget_status = "caution"
            budget_message = "Budget usage moderate - continue monitoring"
        else:
            budget_status = "healthy"
            budget_message = "Budget usage within normal range"
        
        # Cost optimization recommendations
        recommendations = []
        
        if cache_hit_rate < 70:
            recommendations.append({
                "type": "cache_optimization",
                "priority": "high",
                "message": "Increase cache hit rate to reduce LLM API calls",
                "action": f"Current hit rate: {cache_hit_rate:.1f}%, target: 70%+"
            })
        
        if budget_used_pct > 50:
            recommendations.append({
                "type": "batch_optimization",
                "priority": "medium",
                "message": "Consider increasing batch size for LLM calls",
                "action": f"Current batch size: {settings.LLM_BATCH_SIZE}, consider increasing to 25-30"
            })
        
        if llm_cost_info.get("daily_cost_eur", 0) > (settings.LLM_MONTHLY_BUDGET / 30):
            recommendations.append({
                "type": "usage_pattern",
                "priority": "medium",
                "message": "Daily usage exceeds average monthly allocation",
                "action": "Monitor usage patterns and consider implementing rate limiting"
            })
        
        return {
            "success": True,
            "budget_status": budget_status,
            "budget_message": budget_message,
            "cost_breakdown": llm_cost_info,
            "infrastructure_costs": {
                "render_monthly_usd": 7,
                "vercel_monthly_usd": 0,
                "github_monthly_usd": 0,
                "total_infrastructure_monthly_usd": 7
            },
            "cache_optimization": {
                "current_hit_rate_percentage": cache_hit_rate,
                "target_hit_rate_percentage": 70,
                "cache_status": "optimal" if cache_hit_rate >= 70 else "needs_improvement",
                "estimated_cost_savings_eur": round(
                    (70 - cache_hit_rate) / 100 * llm_cost_info.get("monthly_cost_eur", 0) * 0.3, 2
                ) if cache_hit_rate < 70 else 0
            },
            "api_quotas": {
                "youtube_api": {
                    "daily_quota": 10000,
                    "cost_per_search": 100,
                    "cost_per_video_details": 1,
                    "estimated_daily_usage": "Variable based on search volume"
                },
                "gemini_flash": {
                    "cost_per_million_tokens": 0.20,
                    "monthly_token_budget": int((settings.LLM_MONTHLY_BUDGET / 0.20) * 1_000_000),
                    "estimated_videos_per_day": int((settings.LLM_MONTHLY_BUDGET * 1_000_000) / (0.20 * 30 * 100))
                }
            },
            "recommendations": recommendations,
            "next_review_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Budget analytics error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching budget analytics")


@router.get("/llm-costs")
async def get_llm_costs_analytics(
    days: int = Query(7, description="Number of days to analyze", ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get detailed LLM cost analytics with token usage breakdown.
    
    **Parameters:**
    - **days**: Number of days to analyze (1-30, default: 7)
    
    **Returns:**
    - Token usage breakdown (input/output)
    - Cost analysis (USD/EUR by day)
    - Model performance metrics
    - Budget utilization trends
    """
    try:
        from app.models.llm_usage_log import LLMUsageLog
        from sqlalchemy import func, desc
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Total costs and tokens
        cost_totals = db.query(
            func.sum(LLMUsageLog.cost_usd).label('total_cost_usd'),
            func.sum(LLMUsageLog.input_tokens).label('total_input_tokens'),
            func.sum(LLMUsageLog.output_tokens).label('total_output_tokens'),
            func.count(LLMUsageLog.id).label('total_requests'),
            func.avg(LLMUsageLog.processing_time_ms).label('avg_processing_time')
        ).filter(
            LLMUsageLog.created_at >= start_date
        ).first()
        
        # Daily breakdown
        daily_stats = db.query(
            func.date(LLMUsageLog.created_at).label('date'),
            func.sum(LLMUsageLog.cost_usd).label('daily_cost_usd'),
            func.sum(LLMUsageLog.input_tokens).label('daily_input_tokens'),
            func.sum(LLMUsageLog.output_tokens).label('daily_output_tokens'),
            func.count(LLMUsageLog.id).label('daily_requests')
        ).filter(
            LLMUsageLog.created_at >= start_date
        ).group_by(func.date(LLMUsageLog.created_at)).order_by('date').all()
        
        # Country breakdown
        country_stats = db.query(
            LLMUsageLog.country,
            func.sum(LLMUsageLog.cost_usd).label('country_cost_usd'),
            func.sum(LLMUsageLog.input_tokens).label('country_input_tokens'),
            func.sum(LLMUsageLog.output_tokens).label('country_output_tokens'),
            func.count(LLMUsageLog.id).label('country_requests')
        ).filter(
            LLMUsageLog.created_at >= start_date,
            LLMUsageLog.country.isnot(None)
        ).group_by(LLMUsageLog.country).order_by(desc('country_cost_usd')).all()
        
        # Cache hit analysis
        cache_stats = db.query(
            LLMUsageLog.cache_hit,
            func.count(LLMUsageLog.id).label('hit_count'),
            func.sum(LLMUsageLog.cost_usd).label('hit_cost_usd')
        ).filter(
            LLMUsageLog.created_at >= start_date
        ).group_by(LLMUsageLog.cache_hit).all()
        
        # Calculate efficiency metrics
        total_cost_usd = float(cost_totals.total_cost_usd or 0)
        total_requests = cost_totals.total_requests or 0
        cost_per_request = total_cost_usd / total_requests if total_requests > 0 else 0
        
        # Build response
        response = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "totals": {
                "cost_usd": round(total_cost_usd, 6),
                "input_tokens": int(cost_totals.total_input_tokens or 0),
                "output_tokens": int(cost_totals.total_output_tokens or 0),
                "total_tokens": int((cost_totals.total_input_tokens or 0) + (cost_totals.total_output_tokens or 0)),
                "requests": total_requests,
                "avg_processing_time_ms": round(float(cost_totals.avg_processing_time or 0), 2),
                "cost_per_request": round(cost_per_request, 6)
            },
            "daily_breakdown": [
                {
                    "date": str(stat.date),
                    "cost_usd": round(float(stat.daily_cost_usd), 6),
                    "input_tokens": int(stat.daily_input_tokens),
                    "output_tokens": int(stat.daily_output_tokens),
                    "requests": stat.daily_requests
                } for stat in daily_stats
            ],
            "country_breakdown": [
                {
                    "country": stat.country,
                    "cost_usd": round(float(stat.country_cost_usd), 6),
                    "input_tokens": int(stat.country_input_tokens),
                    "output_tokens": int(stat.country_output_tokens),
                    "requests": stat.country_requests
                } for stat in country_stats[:10]  # Top 10 countries
            ],
            "cache_efficiency": {
                stat.cache_hit: {
                    "requests": stat.hit_count,
                    "cost_usd": round(float(stat.hit_cost_usd or 0), 6)
                } for stat in cache_stats
            },
            "model_info": {
                "current_model": "gemini-2.5-flash-lite",
                "input_cost_per_1m_tokens": 0.10,
                "output_cost_per_1m_tokens": 0.40,
                "currency": "USD"
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"LLM costs analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics query failed: {str(e)}")


@router.get("/token-usage")
async def get_token_usage_analytics(
    days: int = Query(7, description="Number of days to analyze", ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get detailed token usage analytics with trends.
    
    **Parameters:**
    - **days**: Number of days to analyze (1-30, default: 7)
    
    **Returns:**
    - Token usage trends over time
    - Input vs output token ratios
    - Efficiency metrics by country and query type
    """
    try:
        from app.models.llm_usage_log import LLMUsageLog
        from sqlalchemy import func
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Hourly token usage for trend analysis
        hourly_usage = db.query(
            func.date_trunc('hour', LLMUsageLog.created_at).label('hour'),
            func.sum(LLMUsageLog.input_tokens).label('input_tokens'),
            func.sum(LLMUsageLog.output_tokens).label('output_tokens'),
            func.count(LLMUsageLog.id).label('requests')
        ).filter(
            LLMUsageLog.created_at >= start_date
        ).group_by(func.date_trunc('hour', LLMUsageLog.created_at)).order_by('hour').all()
        
        # Token efficiency by country
        country_efficiency = db.query(
            LLMUsageLog.country,
            func.avg(LLMUsageLog.input_tokens).label('avg_input_tokens'),
            func.avg(LLMUsageLog.output_tokens).label('avg_output_tokens'),
            func.avg(LLMUsageLog.input_tokens + LLMUsageLog.output_tokens).label('avg_total_tokens'),
            func.avg(LLMUsageLog.processing_time_ms).label('avg_processing_time')
        ).filter(
            LLMUsageLog.created_at >= start_date,
            LLMUsageLog.country.isnot(None)
        ).group_by(LLMUsageLog.country).all()
        
        # Video count vs token usage correlation
        video_efficiency = db.query(
            LLMUsageLog.video_count,
            func.avg(LLMUsageLog.input_tokens).label('avg_input_tokens'),
            func.avg(LLMUsageLog.output_tokens).label('avg_output_tokens'),
            func.count(LLMUsageLog.id).label('request_count')
        ).filter(
            LLMUsageLog.created_at >= start_date,
            LLMUsageLog.video_count.isnot(None)
        ).group_by(LLMUsageLog.video_count).order_by(LLMUsageLog.video_count).all()
        
        response = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "hourly_trends": [
                {
                    "hour": stat.hour.isoformat(),
                    "input_tokens": int(stat.input_tokens),
                    "output_tokens": int(stat.output_tokens),
                    "total_tokens": int(stat.input_tokens + stat.output_tokens),
                    "requests": stat.requests,
                    "tokens_per_request": round((stat.input_tokens + stat.output_tokens) / stat.requests, 2) if stat.requests > 0 else 0
                } for stat in hourly_usage
            ],
            "country_efficiency": [
                {
                    "country": stat.country,
                    "avg_input_tokens": round(float(stat.avg_input_tokens), 2),
                    "avg_output_tokens": round(float(stat.avg_output_tokens), 2),
                    "avg_total_tokens": round(float(stat.avg_total_tokens), 2),
                    "avg_processing_time_ms": round(float(stat.avg_processing_time), 2),
                    "input_output_ratio": round(float(stat.avg_input_tokens) / float(stat.avg_output_tokens), 2) if stat.avg_output_tokens > 0 else 0
                } for stat in country_efficiency
            ],
            "video_scaling": [
                {
                    "video_count": stat.video_count,
                    "avg_input_tokens": round(float(stat.avg_input_tokens), 2),
                    "avg_output_tokens": round(float(stat.avg_output_tokens), 2),
                    "request_count": stat.request_count,
                    "tokens_per_video": round(float(stat.avg_input_tokens + stat.avg_output_tokens) / stat.video_count, 2) if stat.video_count > 0 else 0
                } for stat in video_efficiency if stat.video_count and stat.video_count <= 50  # Reasonable limit
            ]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Token usage analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Token analytics query failed: {str(e)}")


@router.get("/performance")
async def get_performance_analytics(
    hours: int = Query(24, description="Number of hours to analyze", ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get system performance analytics.
    
    **Parameters:**
    - **hours**: Number of hours to analyze (1-168, default: 24)
    
    **Returns:**
    - Response time statistics
    - Cache performance metrics
    - Error rates and system reliability
    - Throughput and capacity metrics
    """
    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=hours)
        
        # Cache performance metrics
        cache_stats = cache.get_cache_stats()
        
        # Search volume metrics
        recent_searches = db.query(SearchCache).filter(
            SearchCache.created_at >= start_date
        ).count()
        
        # Response time estimation (from cache metadata)
        # This would be enhanced with actual response time tracking in production
        estimated_avg_response_time = 3500  # milliseconds (estimated)
        
        # System capacity metrics
        searches_per_hour = recent_searches / max(hours, 1)
        peak_capacity_estimate = 100  # searches per hour (conservative estimate)
        
        capacity_utilization = (searches_per_hour / peak_capacity_estimate) * 100
        
        return {
            "success": True,
            "analysis_period": {
                "hours": hours,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "performance_metrics": {
                "estimated_avg_response_time_ms": estimated_avg_response_time,
                "target_response_time_ms": settings.MAX_RESPONSE_TIME * 1000,
                "response_time_status": "good" if estimated_avg_response_time < (settings.MAX_RESPONSE_TIME * 1000) else "needs_improvement"
            },
            "throughput_metrics": {
                "searches_in_period": recent_searches,
                "searches_per_hour": round(searches_per_hour, 2),
                "peak_capacity_estimate": peak_capacity_estimate,
                "capacity_utilization_percentage": round(capacity_utilization, 1)
            },
            "cache_metrics": cache_stats,
            "reliability_metrics": {
                "estimated_uptime_percentage": 99.5,  # Would be tracked in production
                "error_rate_percentage": 0.1,  # Would be tracked in production
                "availability_target": 99.0
            },
            "optimization_suggestions": [
                {
                    "metric": "cache_hit_rate",
                    "current": cache_stats.get("hit_rate_percentage", 0),
                    "target": 70,
                    "suggestion": "Increase cache TTL if hit rate is below 70%" if cache_stats.get("hit_rate_percentage", 0) < 70 else "Cache performance is optimal"
                },
                {
                    "metric": "capacity_utilization", 
                    "current": capacity_utilization,
                    "target": 80,
                    "suggestion": "Consider scaling up if utilization consistently exceeds 80%" if capacity_utilization > 80 else "Capacity utilization is healthy"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Performance analytics error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching performance analytics")