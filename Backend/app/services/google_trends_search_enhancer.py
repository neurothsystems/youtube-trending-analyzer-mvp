import logging
import time
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
import random
from app.core.config import settings
from app.core.redis import cache
from app.services.country_processors import CountryProcessorFactory
from app.services.robust_google_trends import robust_google_trends

logger = logging.getLogger(__name__)


class GoogleTrendsSearchEnhancer:
    """Enhanced search term generation using robust Google Trends wrapper."""
    
    def __init__(self):
        """Initialize Google Trends search enhancer with robust wrapper."""
        self.robust_trends = robust_google_trends
        logger.info("Google Trends Search Enhancer initialized with robust wrapper")
    
    def _is_available(self) -> bool:
        """Check if Google Trends is available and healthy."""
        return self.robust_trends.is_healthy()
    
    def _get_cache_key(self, query: str, country: str, timeframe: str) -> str:
        """Generate cache key for enhanced search terms."""
        return f"enhanced_search:{country.upper()}:{query.lower()}:{timeframe}"
    
    def get_service_stats(self) -> Dict:
        """Get comprehensive service statistics from robust wrapper."""
        return self.robust_trends.get_stats()
    
    def get_enhanced_search_terms(self, query: str, country: str, timeframe: str = '7d') -> List[str]:
        """
        Get enhanced search terms using Google Trends data.
        
        Strategy:
        1. Original query
        2. Top Related Topic from Web Search (cleaned)
        3. Top 5 YouTube Search Queries
        
        Returns: Maximum 7 search terms (1 + 1 + 5)
        """
        if not self._is_available():
            logger.warning("Google Trends not available, using original query only (no fallback)")
            return [query]  # Return only original query as per user requirement
        
        # Check cache first
        cache_key = self._get_cache_key(query, country, timeframe)
        cached_terms = cache.get(cache_key)
        if cached_terms:
            logger.info(f"Retrieved enhanced search terms from cache for '{query}' in {country}")
            return cached_terms
        
        try:
            enhanced_terms = []
            
            # 1. Always include original query
            enhanced_terms.append(query)
            
            # 2. Get top related topic from web search
            web_topic = self._get_top_web_topic(query, country, timeframe)
            if web_topic and web_topic.lower() != query.lower():
                enhanced_terms.append(web_topic)
            
            # 3. Get top YouTube search queries
            youtube_queries = self._get_youtube_search_queries(query, country, timeframe)
            enhanced_terms.extend(youtube_queries[:5])  # Max 5 YouTube queries
            
            # Remove duplicates while preserving order
            unique_terms = []
            seen = set()
            for term in enhanced_terms:
                term_lower = term.lower().strip()
                if term_lower and term_lower not in seen:
                    unique_terms.append(term)
                    seen.add(term_lower)
            
            # Limit to 7 terms total
            final_terms = unique_terms[:7]
            
            # Cache the results (TTL: 2 hours)
            cache.set(cache_key, final_terms, ttl=7200)
            
            logger.info(f"Enhanced search terms for '{query}' in {country}: {final_terms}")
            return final_terms
            
        except Exception as e:
            logger.error(f"Error getting enhanced search terms for '{query}': {e}")
            return [query]  # No fallback - only original query
    
    def _get_top_web_topic(self, query: str, country: str, timeframe: str) -> Optional[str]:
        """Get top related topic from web search using robust wrapper."""
        try:
            # Use robust Google Trends wrapper
            related_topics = self.robust_trends.get_related_topics(query, country, timeframe)
            
            if (related_topics and 
                query in related_topics and 
                related_topics[query] and 
                'top' in related_topics[query] and 
                related_topics[query]['top'] is not None and 
                not related_topics[query]['top'].empty):
                
                # Get the top topic
                top_topic_row = related_topics[query]['top'].iloc[0]
                topic_title = top_topic_row['topic_title']
                
                # Clean the topic title (remove "- Topic" suffix)
                cleaned_topic = topic_title.replace(' - Topic', '').replace(' - Thema', '').strip()
                
                logger.info(f"Top web topic for '{query}': {cleaned_topic}")
                return cleaned_topic
            
            logger.info(f"No web topics found for '{query}' in {country}")
            return None
            
        except Exception as e:
            logger.warning(f"Error getting web topics for '{query}': {e}")
            return None
    
    def _get_youtube_search_queries(self, query: str, country: str, timeframe: str) -> List[str]:
        """Get top YouTube search queries using robust wrapper."""
        try:
            # Use robust Google Trends wrapper for YouTube queries
            related_queries = self.robust_trends.get_related_queries(query, country, timeframe, 'youtube')
            
            youtube_terms = []
            
            if (related_queries and 
                query in related_queries and 
                related_queries[query] and 
                'top' in related_queries[query] and 
                related_queries[query]['top'] is not None and 
                not related_queries[query]['top'].empty):
                
                # Get top 5 YouTube search queries
                top_queries = related_queries[query]['top']['query'].head(5).tolist()
                youtube_terms.extend(top_queries)
                
                logger.info(f"Top YouTube queries for '{query}': {top_queries}")
            
            # If we have rising queries and not enough top queries, add some rising ones
            if (len(youtube_terms) < 5 and 
                query in related_queries and
                related_queries[query] and
                'rising' in related_queries[query] and 
                related_queries[query]['rising'] is not None and 
                not related_queries[query]['rising'].empty):
                
                needed_count = 5 - len(youtube_terms)
                rising_queries = related_queries[query]['rising']['query'].head(needed_count).tolist()
                youtube_terms.extend(rising_queries)
                
                logger.info(f"Added rising YouTube queries for '{query}': {rising_queries}")
            
            return youtube_terms[:5]  # Ensure max 5 terms
            
        except Exception as e:
            logger.warning(f"Error getting YouTube queries for '{query}': {e}")
            return []
    
    # Fallback method removed as per user requirement - no fallbacks, only original query
    
    def get_search_terms_with_metadata(self, query: str, country: str, timeframe: str = '7d') -> Dict:
        """
        Get enhanced search terms with metadata for transparency.
        
        Returns:
        {
            'search_terms': List[str],
            'source': 'google_trends' | 'fallback',
            'web_topic': str | None,
            'youtube_queries': List[str],
            'cache_hit': bool,
            'error': str | None
        }
        """
        cache_key = self._get_cache_key(query, country, timeframe)
        cached_result = cache.get(f"{cache_key}_metadata")
        
        if cached_result:
            cached_result['cache_hit'] = True
            return cached_result
        
        result = {
            'search_terms': [],
            'source': 'google_trends',
            'web_topic': None,
            'youtube_queries': [],
            'cache_hit': False,
            'error': None
        }
        
        if not self._is_available():
            result['source'] = 'fallback'
            result['search_terms'] = [query]  # No fallback - only original query
            result['error'] = 'Google Trends not available'
        else:
            try:
                # Get enhanced terms with details
                result['search_terms'] = [query]  # Always start with original
                
                # Get web topic
                web_topic = self._get_top_web_topic(query, country, timeframe)
                if web_topic:
                    result['web_topic'] = web_topic
                    result['search_terms'].append(web_topic)
                
                # Get YouTube queries
                youtube_queries = self._get_youtube_search_queries(query, country, timeframe)
                result['youtube_queries'] = youtube_queries
                result['search_terms'].extend(youtube_queries)
                
                # Remove duplicates
                unique_terms = []
                seen = set()
                for term in result['search_terms']:
                    term_lower = term.lower().strip()
                    if term_lower and term_lower not in seen:
                        unique_terms.append(term)
                        seen.add(term_lower)
                
                result['search_terms'] = unique_terms[:7]
                
            except Exception as e:
                logger.error(f"Error in enhanced search with metadata: {e}")
                result['source'] = 'fallback'
                result['search_terms'] = [query]  # No fallback - only original query
                result['error'] = str(e)
        
        # Cache the result with metadata
        cache.set(f"{cache_key}_metadata", result, ttl=7200)
        
        return result


# Create global instance
google_trends_search_enhancer = GoogleTrendsSearchEnhancer()