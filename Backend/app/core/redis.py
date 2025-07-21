import redis
import json
import logging
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache client for budget optimization."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.client:
            return None
            
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.client:
            return False
            
        try:
            serialized_value = json.dumps(value, default=str)
            
            if ttl:
                return self.client.setex(key, ttl, serialized_value)
            else:
                return self.client.set(key, serialized_value)
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.client:
            return False
            
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.client:
            return False
            
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get TTL for a key."""
        if not self.client:
            return -1
            
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return -1
    
    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.client:
            return 0
            
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis FLUSH_PATTERN error for pattern '{pattern}': {e}")
            return 0
    
    def get_info(self) -> dict:
        """Get Redis server info."""
        if not self.client:
            return {"status": "disconnected"}
            
        try:
            info = self.client.info()
            return {
                "status": "connected",
                "version": info.get("redis_version", "unknown"),
                "memory_used": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Redis INFO error: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        info = self.get_info()
        
        if info["status"] != "connected":
            return info
        
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        hit_rate = hits / total if total > 0 else 0.0
        
        return {
            "status": "connected",
            "hits": hits,
            "misses": misses,
            "hit_rate": hit_rate,
            "hit_rate_percentage": round(hit_rate * 100, 2),
            "target_hit_rate": settings.TARGET_CACHE_HIT_RATE * 100,
            "memory_used": info.get("memory_used", "unknown"),
            "connected_clients": info.get("connected_clients", 0)
        }


# Create global cache instance
cache = RedisCache()


def get_trending_cache_key(query: str, country: str, timeframe: str) -> str:
    """Generate cache key for trending search."""
    return f"trending:{country.upper()}:{query.lower()}:{timeframe}"


def get_video_cache_key(video_id: str) -> str:
    """Generate cache key for video data."""
    return f"video:{video_id}"


def get_trending_feed_cache_key(country: str) -> str:
    """Generate cache key for trending feed."""
    return f"trending_feed:{country.upper()}"


def get_llm_cache_key(video_ids: list, country: str) -> str:
    """Generate cache key for LLM analysis."""
    video_ids_str = ",".join(sorted(video_ids))
    import hashlib
    hash_key = hashlib.sha256(f"{video_ids_str}:{country}".encode()).hexdigest()[:16]
    return f"llm:{country}:{hash_key}"


class CacheManager:
    """High-level cache management for specific use cases."""
    
    @staticmethod
    def get_trending_results(query: str, country: str, timeframe: str) -> Optional[dict]:
        """Get cached trending results."""
        cache_key = get_trending_cache_key(query, country, timeframe)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_trending_results(query: str, country: str, timeframe: str, results: dict) -> bool:
        """Cache trending results with appropriate TTL."""
        cache_key = get_trending_cache_key(query, country, timeframe)
        ttl = settings.CACHE_TTL_SEARCH  # 2 hours
        return cache.set(cache_key, results, ttl)
    
    @staticmethod
    def get_video_data(video_id: str) -> Optional[dict]:
        """Get cached video data."""
        cache_key = get_video_cache_key(video_id)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_video_data(video_id: str, video_data: dict) -> bool:
        """Cache video data with appropriate TTL."""
        cache_key = get_video_cache_key(video_id)
        ttl = settings.CACHE_TTL_VIDEO  # 24 hours
        return cache.set(cache_key, video_data, ttl)
    
    @staticmethod
    def get_trending_feed(country: str) -> Optional[list]:
        """Get cached trending feed."""
        cache_key = get_trending_feed_cache_key(country)
        return cache.get(cache_key)
    
    @staticmethod
    def cache_trending_feed(country: str, feed_data: list) -> bool:
        """Cache trending feed with appropriate TTL."""
        cache_key = get_trending_feed_cache_key(country)
        ttl = settings.CACHE_TTL_TRENDING  # 1 hour
        return cache.set(cache_key, feed_data, ttl)
    
    @staticmethod
    def invalidate_country_cache(country: str) -> int:
        """Invalidate all cache entries for a country."""
        patterns = [
            f"trending:{country.upper()}:*",
            f"trending_feed:{country.upper()}",
            f"llm:{country}:*"
        ]
        
        deleted = 0
        for pattern in patterns:
            deleted += cache.flush_pattern(pattern)
        
        logger.info(f"Invalidated {deleted} cache entries for country {country}")
        return deleted