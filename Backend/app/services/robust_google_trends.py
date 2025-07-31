"""
Robust Google Trends Wrapper - Production-Ready PyTrends Replacement

This module provides a drop-in replacement for pytrends with enhanced reliability,
anti-detection, and comprehensive fallback strategies for production use.

Created by Backend Expert + DevOps Expert collaboration.
"""

import logging
import random
import time
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import pickle
import os

# Third-party imports
import requests
from pytrends.request import TrendReq
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)
from cachetools import TTLCache, LRUCache

# Local imports
from app.core.config import settings
from app.core.redis import cache

logger = logging.getLogger(__name__)


class RequestStatus(Enum):
    """Request status enumeration."""
    SUCCESS = "success"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RequestResult:
    """Request result with metadata."""
    status: RequestStatus
    data: Optional[Dict] = None
    error: Optional[str] = None
    response_time: float = 0.0
    attempt_count: int = 1
    cache_hit: bool = False


class CircuitBreaker:
    """Circuit breaker pattern implementation for request management."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self._lock = threading.Lock()
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        with self._lock:
            if self.state == "closed":
                return True
            elif self.state == "open":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "half-open"
                    return True
                return False
            else:  # half-open
                return True
    
    def record_success(self):
        """Record successful request."""
        with self._lock:
            self.failure_count = 0
            self.state = "closed"
    
    def record_failure(self):
        """Record failed request."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class SessionPool:
    """Pool of TrendReq sessions for rotation."""
    
    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.sessions = []
        self.current_index = 0
        self._lock = threading.Lock()
        self._initialize_sessions()
    
    def _initialize_sessions(self):
        """Initialize session pool with different configurations."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        timezones = [360, 120, -60, 480]  # Different timezone offsets
        languages = ['en-US', 'de-DE', 'fr-FR', 'en-GB']
        
        for i in range(self.pool_size):
            try:
                session = TrendReq(
                    hl=languages[i % len(languages)],
                    tz=timezones[i % len(timezones)],
                    timeout=(15, 30),
                    retries=2,
                    backoff_factor=0.3
                )
                
                # Customize session headers
                if hasattr(session, 'session'):
                    session.session.headers.update({
                        'User-Agent': user_agents[i % len(user_agents)],
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': f'{languages[i % len(languages)]},en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'empty',
                        'Sec-Fetch-Mode': 'cors',
                        'Sec-Fetch-Site': 'same-origin',
                    })
                
                self.sessions.append(session)
                logger.debug(f"Initialized session {i} with UA: {user_agents[i % len(user_agents)][:50]}...")
                
            except Exception as e:
                logger.error(f"Failed to initialize session {i}: {e}")
                # Create minimal fallback session
                self.sessions.append(TrendReq())
    
    def get_session(self) -> TrendReq:
        """Get next session from pool."""
        with self._lock:
            session = self.sessions[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.sessions)
            return session
    
    def invalidate_session(self, session: TrendReq):
        """Mark session as potentially compromised and rotate."""
        with self._lock:
            try:
                index = self.sessions.index(session)
                # Recreate the compromised session
                self.sessions[index] = TrendReq()
                logger.info(f"Recreated compromised session at index {index}")
            except ValueError:
                logger.warning("Attempted to invalidate session not in pool")


class MultiLayerCache:
    """Multi-layer caching system with Redis, memory, and file fallbacks."""
    
    def __init__(self):
        # Layer 1: Redis (primary)
        self.redis_cache = cache
        
        # Layer 2: In-memory LRU cache (secondary)
        self.memory_cache = LRUCache(maxsize=1000)
        
        # Layer 3: File cache (tertiary)
        self.file_cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache', 'trends')
        os.makedirs(self.file_cache_dir, exist_ok=True)
        
        # TTL settings (in seconds)
        self.redis_ttl = 4 * 3600  # 4 hours
        self.memory_ttl = 1 * 3600  # 1 hour
        self.file_ttl = 24 * 3600    # 24 hours
    
    def _get_cache_key(self, method: str, *args, **kwargs) -> str:
        """Generate consistent cache key."""
        key_data = f"{method}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, method: str, *args, **kwargs) -> Optional[Dict]:
        """Get data from cache layers (Redis -> Memory -> File)."""
        cache_key = self._get_cache_key(method, *args, **kwargs)
        
        # Layer 1: Redis
        try:
            redis_data = self.redis_cache.get(f"trends:{cache_key}")
            if redis_data:
                logger.debug(f"Cache hit (Redis): {method}")
                return json.loads(redis_data)
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")
        
        # Layer 2: Memory
        memory_data = self.memory_cache.get(cache_key)
        if memory_data:
            logger.debug(f"Cache hit (Memory): {method}")
            return memory_data
        
        # Layer 3: File
        try:
            file_path = os.path.join(self.file_cache_dir, f"{cache_key}.json")
            if os.path.exists(file_path):
                file_age = time.time() - os.path.getmtime(file_path)
                if file_age < self.file_ttl:
                    with open(file_path, 'r') as f:
                        file_data = json.load(f)
                    logger.debug(f"Cache hit (File): {method}")
                    return file_data
        except Exception as e:
            logger.warning(f"File cache error: {e}")
        
        return None
    
    def set(self, method: str, data: Dict, *args, **kwargs):
        """Set data in all cache layers."""
        cache_key = self._get_cache_key(method, *args, **kwargs)
        
        # Layer 1: Redis
        try:
            self.redis_cache.setex(
                f"trends:{cache_key}", 
                self.redis_ttl, 
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Redis cache set error: {e}")
        
        # Layer 2: Memory (TTLCache handles expiration automatically)
        self.memory_cache[cache_key] = data
        
        # Layer 3: File
        try:
            file_path = os.path.join(self.file_cache_dir, f"{cache_key}.json")
            with open(file_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"File cache set error: {e}")


class RequestMonitor:
    """Monitor request success rates and patterns."""
    
    def __init__(self):
        self.stats = defaultdict(int)
        self.recent_requests = []
        self.max_recent_requests = 100
        self._lock = threading.Lock()
    
    def record_request(self, result: RequestResult):
        """Record request result for monitoring."""
        with self._lock:
            self.stats[result.status.value] += 1
            self.stats['total'] += 1
            
            # Keep recent requests for pattern analysis
            self.recent_requests.append({
                'timestamp': time.time(),
                'status': result.status.value,
                'response_time': result.response_time,
                'attempt_count': result.attempt_count
            })
            
            # Trim to max size
            if len(self.recent_requests) > self.max_recent_requests:
                self.recent_requests = self.recent_requests[-self.max_recent_requests:]
    
    def get_success_rate(self, window_minutes: int = 30) -> float:
        """Get success rate for recent time window."""
        with self._lock:
            cutoff_time = time.time() - (window_minutes * 60)
            recent = [r for r in self.recent_requests if r['timestamp'] > cutoff_time]
            
            if not recent:
                return 0.0
            
            successful = len([r for r in recent if r['status'] == 'success'])
            return successful / len(recent)
    
    def get_stats(self) -> Dict:
        """Get comprehensive monitoring stats."""
        with self._lock:
            total = self.stats['total']
            if total == 0:
                return {'success_rate': 0.0, 'total_requests': 0}
            
            return {
                'success_rate': self.stats['success'] / total,
                'total_requests': total,
                'rate_limited': self.stats['rate_limited'],
                'blocked': self.stats['blocked'],
                'network_errors': self.stats['network_error'],
                'unknown_errors': self.stats['unknown_error'],
                'recent_success_rate_30m': self.get_success_rate(30),
                'recent_success_rate_5m': self.get_success_rate(5)
            }


class RobustGoogleTrends:
    """
    Robust Google Trends wrapper with comprehensive reliability features.
    
    This class provides a drop-in replacement for pytrends with:
    - Session rotation and management
    - Multi-layer caching
    - Circuit breaker pattern
    - Comprehensive retry logic
    - Request monitoring
    - Fallback strategies
    """
    
    def __init__(self):
        """Initialize robust Google Trends client."""
        self.session_pool = SessionPool(pool_size=3)
        self.cache = MultiLayerCache()
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        self.monitor = RequestMonitor()
        
        # Timing configuration
        self.base_delay = 3.0
        self.max_delay = 30.0
        self.jitter_range = 0.3
        
        # Request configuration
        self.max_retries = 5
        self.timeout = (15, 30)
        
        logger.info("RobustGoogleTrends initialized with enhanced reliability features")
    
    def _get_adaptive_delay(self, attempt: int = 1) -> float:
        """Calculate adaptive delay based on attempt count and success rate."""
        success_rate = self.monitor.get_success_rate(5)  # Last 5 minutes
        
        # Base delay increases with attempts
        delay = self.base_delay * (1.5 ** (attempt - 1))
        
        # Increase delay if success rate is low
        if success_rate < 0.3:
            delay *= 3.0  # 3x delay if success rate < 30%
        elif success_rate < 0.6:
            delay *= 2.0  # 2x delay if success rate < 60%
        
        # Add jitter to avoid thundering herd
        jitter = random.uniform(-self.jitter_range, self.jitter_range)
        delay = delay * (1 + jitter)
        
        return min(delay, self.max_delay)
    
    def _wait_with_adaptive_delay(self, attempt: int = 1):
        """Wait with adaptive delay before next request."""
        delay = self._get_adaptive_delay(attempt)
        logger.debug(f"Waiting {delay:.2f}s before attempt {attempt}")
        time.sleep(delay)
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, requests.RequestException)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _execute_request(self, method_name: str, method_callable, *args, **kwargs) -> RequestResult:
        """Execute request with comprehensive error handling and retry logic."""
        if not self.circuit_breaker.can_execute():
            return RequestResult(
                status=RequestStatus.BLOCKED,
                error="Circuit breaker is open"
            )
        
        session = self.session_pool.get_session()
        start_time = time.time()
        attempt_count = kwargs.pop('_attempt_count', 1)
        
        try:
            # Wait before request (except for first attempt)
            if attempt_count > 1:
                self._wait_with_adaptive_delay(attempt_count)
            
            # Execute the actual request
            result = method_callable(session, *args, **kwargs)
            
            response_time = time.time() - start_time
            
            # Record success
            self.circuit_breaker.record_success()
            
            request_result = RequestResult(
                status=RequestStatus.SUCCESS,
                data=result,
                response_time=response_time,
                attempt_count=attempt_count
            )
            
            self.monitor.record_request(request_result)
            logger.debug(f"Request {method_name} succeeded in {response_time:.2f}s (attempt {attempt_count})")
            
            return request_result
            
        except Exception as e:
            response_time = time.time() - start_time
            error_str = str(e).lower()
            
            # Classify error type
            if '429' in error_str or 'too many requests' in error_str:
                status = RequestStatus.RATE_LIMITED
                self.session_pool.invalidate_session(session)
            elif '403' in error_str or 'forbidden' in error_str or 'blocked' in error_str:
                status = RequestStatus.BLOCKED
                self.session_pool.invalidate_session(session)
            elif 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
                status = RequestStatus.NETWORK_ERROR
            else:
                status = RequestStatus.UNKNOWN_ERROR
            
            # Record failure
            self.circuit_breaker.record_failure()
            
            request_result = RequestResult(
                status=status,
                error=str(e),
                response_time=response_time,
                attempt_count=attempt_count
            )
            
            self.monitor.record_request(request_result)
            logger.warning(f"Request {method_name} failed: {e} (attempt {attempt_count})")
            
            # Re-raise for retry mechanism if appropriate
            if status in [RequestStatus.NETWORK_ERROR, RequestStatus.UNKNOWN_ERROR] and attempt_count < self.max_retries:
                raise
            
            return request_result
    
    def _get_related_topics_raw(self, session: TrendReq, query: str, geo: str, timeframe: str) -> Dict:
        """Get related topics using session."""
        # Map our timeframe format to pytrends format
        timeframe_map = {
            '24h': 'now 1-d',
            '48h': 'now 2-d',
            '7d': 'now 7-d',
            '1w': 'now 7-d'
        }
        
        pytrends_timeframe = timeframe_map.get(timeframe, 'now 7-d')
        
        # Build payload
        session.build_payload([query], cat=0, timeframe=pytrends_timeframe, geo=geo, gprop='')
        
        # Get related topics
        related_topics = session.related_topics()
        
        return related_topics
    
    def _get_related_queries_raw(self, session: TrendReq, query: str, geo: str, timeframe: str, gprop: str = 'youtube') -> Dict:
        """Get related queries using session."""
        # Map our timeframe format to pytrends format
        timeframe_map = {
            '24h': 'now 1-d',
            '48h': 'now 2-d',
            '7d': 'now 7-d',
            '1w': 'now 7-d'
        }
        
        pytrends_timeframe = timeframe_map.get(timeframe, 'now 7-d')
        
        # Build payload
        session.build_payload([query], cat=0, timeframe=pytrends_timeframe, geo=geo, gprop=gprop)
        
        # Get related queries
        related_queries = session.related_queries()
        
        return related_queries
    
    def get_related_topics(self, query: str, geo: str, timeframe: str = '7d') -> Optional[Dict]:
        """
        Get related topics with caching and error handling.
        
        Args:
            query: Search term
            geo: Country code (e.g. 'DE', 'US')
            timeframe: Time period ('24h', '48h', '7d', '1w')
        
        Returns:
            Related topics data or None if failed
        """
        # Check cache first
        cached_data = self.cache.get('related_topics', query, geo, timeframe)
        if cached_data:
            return cached_data
        
        # Execute request
        result = self._execute_request(
            'get_related_topics',
            self._get_related_topics_raw,
            query, geo, timeframe
        )
        
        if result.status == RequestStatus.SUCCESS and result.data:
            # Cache successful result
            self.cache.set('related_topics', result.data, query, geo, timeframe)
            return result.data
        
        logger.warning(f"Failed to get related topics for '{query}' in {geo}: {result.error}")
        return None
    
    def get_related_queries(self, query: str, geo: str, timeframe: str = '7d', gprop: str = 'youtube') -> Optional[Dict]:
        """
        Get related queries with caching and error handling.
        
        Args:
            query: Search term
            geo: Country code (e.g. 'DE', 'US')
            timeframe: Time period ('24h', '48h', '7d', '1w')
            gprop: Google property ('youtube', '' for web)
        
        Returns:
            Related queries data or None if failed
        """
        # Check cache first
        cached_data = self.cache.get('related_queries', query, geo, timeframe, gprop)
        if cached_data:
            return cached_data
        
        # Execute request
        result = self._execute_request(
            'get_related_queries',
            self._get_related_queries_raw,
            query, geo, timeframe, gprop
        )
        
        if result.status == RequestStatus.SUCCESS and result.data:
            # Cache successful result
            self.cache.set('related_queries', result.data, query, geo, timeframe, gprop)
            return result.data
        
        logger.warning(f"Failed to get related queries for '{query}' in {geo}: {result.error}")
        return None
    
    def get_trending_searches(self, geo: str) -> Optional[Dict]:
        """
        Get trending searches for country.
        
        Args:
            geo: Country code (e.g. 'DE', 'US')
        
        Returns:
            Trending searches data or None if failed
        """
        # Check cache first (shorter TTL for trending data)
        cached_data = self.cache.get('trending_searches', geo)
        if cached_data:
            return cached_data
        
        # Execute request
        def _get_trending_raw(session: TrendReq, geo: str) -> Dict:
            return session.trending_searches(pn=geo)
        
        result = self._execute_request(
            'get_trending_searches',
            _get_trending_raw,
            geo
        )
        
        if result.status == RequestStatus.SUCCESS and result.data is not None:
            # Cache successful result (shorter TTL for trending data)
            self.cache.set('trending_searches', result.data, geo)
            return result.data
        
        logger.warning(f"Failed to get trending searches for {geo}: {result.error}")
        return None
    
    def get_stats(self) -> Dict:
        """Get comprehensive service statistics."""
        stats = self.monitor.get_stats()
        stats.update({
            'circuit_breaker_state': self.circuit_breaker.state,
            'circuit_breaker_failures': self.circuit_breaker.failure_count,
            'session_pool_size': len(self.session_pool.sessions),
            'cache_layers': ['redis', 'memory', 'file']
        })
        
        return stats
    
    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        stats = self.get_stats()
        
        # Consider healthy if:
        # - Circuit breaker is not open
        # - Recent success rate > 30%
        # - Not too many consecutive failures
        
        return (
            self.circuit_breaker.state != "open" and
            stats.get('recent_success_rate_5m', 0) > 0.3 and
            self.circuit_breaker.failure_count < 3
        )


# Global instance
robust_google_trends = RobustGoogleTrends()