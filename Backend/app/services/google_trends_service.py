import logging
import time
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from pytrends.request import TrendReq
import random
from app.core.config import settings
from app.core.redis import CacheManager

logger = logging.getLogger(__name__)


class GoogleTrendsService:
    """Google Trends integration service for cross-platform validation."""
    
    def __init__(self):
        """Initialize Google Trends client."""
        try:
            self.pytrends = TrendReq(
                hl='en-US', 
                tz=360, 
                timeout=(10, 25),
                retries=2,
                backoff_factor=0.1
            )
            logger.info("Google Trends client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Trends client: {e}")
            self.pytrends = None
    
    def _is_available(self) -> bool:
        """Check if Google Trends is available."""
        return self.pytrends is not None
    
    def _get_cache_key(self, query: str, country: str, timeframe: str) -> str:
        """Generate cache key for Google Trends data."""
        return f"google_trends:{country.upper()}:{query.lower()}:{timeframe}"
    
    def _rate_limit_delay(self):
        """Add random delay to avoid rate limiting."""
        delay = random.uniform(1, 3)  # 1-3 seconds random delay
        time.sleep(delay)
    
    def get_trend_score(self, query: str, country: str, timeframe: str = '7d') -> Dict:
        """
        Get Google Trends score for a query in a specific country.
        
        Returns:
        {
            'trend_score': float,      # 0.0-1.0 normalized score
            'peak_interest': int,      # Peak interest value (0-100)
            'average_interest': float, # Average interest over period
            'is_trending': bool,       # Whether currently trending (high recent interest)
            'timeframe': str,          # Requested timeframe
            'data_points': int,        # Number of data points available
            'cache_hit': bool          # Whether data came from cache
        }
        """
        if not self._is_available():
            logger.error("Google Trends not available")
            return self._empty_result(query, country, timeframe, "Service unavailable")
        
        # Check cache first
        cache_key = self._get_cache_key(query, country, timeframe)
        cached_result = CacheManager.cache.get(cache_key)
        if cached_result:
            cached_result['cache_hit'] = True
            logger.info(f"Retrieved Google Trends from cache for '{query}' in {country}")
            return cached_result
        
        try:
            # Rate limiting
            self._rate_limit_delay()
            
            # Map timeframes
            timeframe_map = {
                '24h': 'now 1-d',
                '48h': 'now 2-d', 
                '7d': 'now 7-d',
                '1w': 'now 7-d',
                '1m': 'now 1-m'
            }
            
            pytrends_timeframe = timeframe_map.get(timeframe, 'now 7-d')
            
            # Build payload for Google Trends
            self.pytrends.build_payload(
                [query], 
                cat=0,  # All categories
                timeframe=pytrends_timeframe,
                geo=country,
                gprop=''  # Web search (default)
            )
            
            # Get interest over time
            interest_data = self.pytrends.interest_over_time()
            
            if interest_data.empty or query not in interest_data.columns:
                logger.warning(f"No Google Trends data found for '{query}' in {country}")
                return self._empty_result(query, country, timeframe, "No data available")
            
            # Calculate metrics
            interest_values = interest_data[query].values
            peak_interest = int(max(interest_values))
            average_interest = float(interest_values.mean())
            
            # Calculate trend score (0.0-1.0)
            # Higher score for higher peak and recent activity
            recent_values = interest_values[-3:] if len(interest_values) >= 3 else interest_values
            recent_average = float(recent_values.mean())
            
            # Normalize to 0-1 scale
            trend_score = min((peak_interest + recent_average) / 200.0, 1.0)
            
            # Determine if currently trending (recent activity > 60% of peak)
            is_trending = recent_average > (peak_interest * 0.6)
            
            result = {
                'trend_score': round(trend_score, 3),
                'peak_interest': peak_interest,
                'average_interest': round(average_interest, 2),
                'recent_interest': round(recent_average, 2),
                'is_trending': is_trending,
                'timeframe': timeframe,
                'data_points': len(interest_values),
                'cache_hit': False,
                'query': query,
                'country': country,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Cache the result (TTL: 2 hours for trends data)
            CacheManager.cache.set(cache_key, result, ttl=7200)
            
            logger.info(f"Google Trends analysis completed for '{query}' in {country}. "
                       f"Score: {trend_score:.3f}, Peak: {peak_interest}")
            
            return result
            
        except Exception as e:
            logger.error(f"Google Trends API error for '{query}' in {country}: {e}")
            return self._empty_result(query, country, timeframe, f"API error: {str(e)}")
    
    def validate_query_trending(self, query: str, country: str, 
                               youtube_trending: bool = False) -> Dict:
        """
        Cross-platform validation between Google Trends and YouTube trends.
        
        Args:
            query: Search query to validate
            country: Target country code
            youtube_trending: Whether query is trending on YouTube
        
        Returns:
        {
            'validation_score': float,    # 0.0-1.0 cross-platform score
            'google_trending': bool,      # Trending on Google
            'youtube_trending': bool,     # Trending on YouTube (input)
            'platform_alignment': str,   # 'strong', 'moderate', 'weak', 'none'
            'recommendation': str,        # Action recommendation
            'google_trends_data': dict    # Full Google Trends data
        }
        """
        # Get Google Trends data
        google_data = self.get_trend_score(query, country)
        
        google_trending = google_data.get('is_trending', False)
        google_score = google_data.get('trend_score', 0.0)
        
        # Calculate cross-platform validation score
        if youtube_trending and google_trending:
            # Both platforms trending - strong validation
            validation_score = min(0.8 + (google_score * 0.2), 1.0)
            alignment = "strong"
            recommendation = "High confidence - trending on both platforms"
            
        elif youtube_trending or google_trending:
            # One platform trending - moderate validation
            validation_score = 0.4 + (google_score * 0.4)
            alignment = "moderate"
            
            if youtube_trending:
                recommendation = f"YouTube trending, Google score: {google_score:.2f}"
            else:
                recommendation = f"Google trending, check YouTube relevance"
                
        elif google_score > 0.3:
            # Some Google interest but not peak trending
            validation_score = google_score * 0.6
            alignment = "weak"
            recommendation = f"Low trending activity (Google score: {google_score:.2f})"
            
        else:
            # No significant trending on either platform
            validation_score = 0.0
            alignment = "none"
            recommendation = "No significant trending activity detected"
        
        return {
            'validation_score': round(validation_score, 3),
            'google_trending': google_trending,
            'youtube_trending': youtube_trending,
            'platform_alignment': alignment,
            'recommendation': recommendation,
            'google_trends_data': google_data,
            'cross_platform_boost': min(validation_score * 0.3, 0.3)  # Max 30% boost
        }
    
    def get_related_queries(self, query: str, country: str) -> List[str]:
        """Get related trending queries from Google Trends."""
        if not self._is_available():
            return []
        
        try:
            self._rate_limit_delay()
            
            self.pytrends.build_payload([query], timeframe='now 7-d', geo=country)
            
            # Get related queries
            related_queries = self.pytrends.related_queries()
            
            if not related_queries or query not in related_queries:
                return []
            
            # Extract top related queries
            top_queries = []
            
            if 'top' in related_queries[query] and related_queries[query]['top'] is not None:
                top_df = related_queries[query]['top']
                top_queries.extend(top_df['query'].head(5).tolist())
            
            if 'rising' in related_queries[query] and related_queries[query]['rising'] is not None:
                rising_df = related_queries[query]['rising']
                top_queries.extend(rising_df['query'].head(3).tolist())
            
            # Remove duplicates and return unique queries
            return list(set(top_queries))[:8]  # Max 8 related queries
            
        except Exception as e:
            logger.error(f"Error getting related queries for '{query}': {e}")
            return []
    
    def _empty_result(self, query: str, country: str, timeframe: str, message: str) -> Dict:
        """Create empty result structure."""
        return {
            'trend_score': 0.0,
            'peak_interest': 0,
            'average_interest': 0.0,
            'recent_interest': 0.0,
            'is_trending': False,
            'timeframe': timeframe,
            'data_points': 0,
            'cache_hit': False,
            'query': query,
            'country': country,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': message
        }


# Create global Google Trends service instance
google_trends_service = GoogleTrendsService()