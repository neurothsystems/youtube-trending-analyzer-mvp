from sqlalchemy import Column, String, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base


class SearchCache(Base):
    """Search results cache model for budget optimization."""
    
    __tablename__ = "search_cache"
    
    # Primary key - hash of query parameters
    cache_key = Column(String(255), primary_key=True, index=True)
    
    # Original query parameters
    query = Column(String(255), index=True)
    country = Column(String(2), index=True) 
    timeframe = Column(String(20), index=True)
    
    # Cached results as JSON
    results = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), index=True)
    
    # Additional indexes
    __table_args__ = (
        Index('idx_expires', 'expires_at'),
        Index('idx_query_country_timeframe', 'query', 'country', 'timeframe'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SearchCache(cache_key='{self.cache_key}', query='{self.query}', country='{self.country}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'cache_key': self.cache_key,
            'query': self.query,
            'country': self.country,
            'timeframe': self.timeframe,
            'results': self.results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def generate_cache_key(cls, query: str, country: str, timeframe: str) -> str:
        """Generate cache key from query parameters."""
        import hashlib
        
        # Create consistent string from parameters
        cache_string = f"trending:{country.upper()}:{query.lower()}:{timeframe}"
        
        # Generate SHA-256 hash
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    @classmethod
    def get_cached_result(cls, db, query: str, country: str, timeframe: str):
        """Get cached result if exists and not expired."""
        from datetime import datetime, timezone
        
        cache_key = cls.generate_cache_key(query, country, timeframe)
        now = datetime.now(timezone.utc)
        
        result = db.query(cls).filter(
            cls.cache_key == cache_key,
            cls.expires_at > now
        ).first()
        
        return result.results if result else None
    
    @classmethod
    def store_result(cls, db, query: str, country: str, timeframe: str, results: dict, ttl_seconds: int):
        """Store search results in cache."""
        from datetime import datetime, timezone, timedelta
        
        cache_key = cls.generate_cache_key(query, country, timeframe)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        
        # Delete existing cache entry if exists
        db.query(cls).filter(cls.cache_key == cache_key).delete()
        
        # Create new cache entry
        cache_entry = cls(
            cache_key=cache_key,
            query=query,
            country=country,
            timeframe=timeframe,
            results=results,
            expires_at=expires_at
        )
        
        db.add(cache_entry)
        db.commit()
        
        return cache_entry
    
    @classmethod
    def cleanup_expired(cls, db) -> int:
        """Remove expired cache entries and return count of deleted entries."""
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        
        expired_count = db.query(cls).filter(cls.expires_at <= now).count()
        db.query(cls).filter(cls.expires_at <= now).delete()
        db.commit()
        
        return expired_count
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if not self.expires_at:
            return True
            
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return now > self.expires_at.replace(tzinfo=timezone.utc)
    
    @property
    def ttl_seconds(self) -> int:
        """Get remaining TTL in seconds."""
        if self.is_expired:
            return 0
            
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        remaining = self.expires_at.replace(tzinfo=timezone.utc) - now
        return int(remaining.total_seconds())