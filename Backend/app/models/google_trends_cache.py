from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from app.models import Base


class GoogleTrendsCache(Base):
    """Google Trends cache model for storing trending data."""
    
    __tablename__ = "google_trends_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(255), nullable=False, index=True)
    country = Column(String(2), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    
    # Google Trends scores
    trend_score = Column(Float, nullable=False)  # 0.0-1.0
    peak_interest = Column(Integer, nullable=False)  # 0-100
    average_interest = Column(Float, nullable=False)
    recent_interest = Column(Float, nullable=False)
    is_trending = Column(Boolean, nullable=False, default=False)
    data_points = Column(Integer, nullable=False, default=0)
    
    # Cross-platform validation
    validation_score = Column(Float, nullable=True)  # 0.0-1.0
    cross_platform_boost = Column(Float, nullable=True)  # 0.0-0.5
    platform_alignment = Column(String(20), nullable=True, default='none')
    
    # Raw data and error handling
    raw_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<GoogleTrendsCache(query='{self.query}', country='{self.country}', trend_score={self.trend_score})>"
    
    @classmethod
    def get_cached_trends(cls, session, query: str, country: str, timeframe: str) -> Optional['GoogleTrendsCache']:
        """Get cached Google Trends data if not expired."""
        now = datetime.now(timezone.utc)
        
        return session.query(cls).filter(
            cls.query == query.lower(),
            cls.country == country.upper(),
            cls.timeframe == timeframe,
            cls.expires_at > now
        ).first()
    
    @classmethod
    def cache_trends_data(cls, session, query: str, country: str, timeframe: str, 
                         trends_data: Dict, ttl_hours: int = 2) -> 'GoogleTrendsCache':
        """Cache Google Trends data with TTL."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
        
        # Check if entry exists
        existing = session.query(cls).filter(
            cls.query == query.lower(),
            cls.country == country.upper(),
            cls.timeframe == timeframe
        ).first()
        
        if existing:
            # Update existing entry
            existing.trend_score = trends_data.get('trend_score', 0.0)
            existing.peak_interest = trends_data.get('peak_interest', 0)
            existing.average_interest = trends_data.get('average_interest', 0.0)
            existing.recent_interest = trends_data.get('recent_interest', 0.0)
            existing.is_trending = trends_data.get('is_trending', False)
            existing.data_points = trends_data.get('data_points', 0)
            existing.validation_score = trends_data.get('validation_score')
            existing.cross_platform_boost = trends_data.get('cross_platform_boost')
            existing.platform_alignment = trends_data.get('platform_alignment', 'none')
            existing.raw_data = trends_data.get('raw_data')
            existing.error_message = trends_data.get('error')
            existing.expires_at = expires_at
            existing.created_at = func.now()
            
            return existing
        else:
            # Create new entry
            new_entry = cls(
                query=query.lower(),
                country=country.upper(),
                timeframe=timeframe,
                trend_score=trends_data.get('trend_score', 0.0),
                peak_interest=trends_data.get('peak_interest', 0),
                average_interest=trends_data.get('average_interest', 0.0),
                recent_interest=trends_data.get('recent_interest', 0.0),
                is_trending=trends_data.get('is_trending', False),
                data_points=trends_data.get('data_points', 0),
                validation_score=trends_data.get('validation_score'),
                cross_platform_boost=trends_data.get('cross_platform_boost'),
                platform_alignment=trends_data.get('platform_alignment', 'none'),
                raw_data=trends_data.get('raw_data'),
                error_message=trends_data.get('error'),
                expires_at=expires_at
            )
            
            session.add(new_entry)
            return new_entry
    
    @classmethod
    def cleanup_expired(cls, session) -> int:
        """Remove expired cache entries."""
        now = datetime.now(timezone.utc)
        
        expired_count = session.query(cls).filter(
            cls.expires_at < now
        ).count()
        
        session.query(cls).filter(
            cls.expires_at < now
        ).delete()
        
        return expired_count
    
    @classmethod
    def get_trending_queries(cls, session, country: str, limit: int = 10):
        """Get currently trending queries for a country."""
        now = datetime.now(timezone.utc)
        
        return session.query(cls).filter(
            cls.country == country.upper(),
            cls.is_trending == True,
            cls.expires_at > now
        ).order_by(cls.trend_score.desc()).limit(limit).all()
    
    @classmethod
    def get_cache_stats(cls, session) -> Dict:
        """Get cache performance statistics."""
        now = datetime.now(timezone.utc)
        
        total_entries = session.query(cls).count()
        valid_entries = session.query(cls).filter(cls.expires_at > now).count()
        expired_entries = total_entries - valid_entries
        
        trending_entries = session.query(cls).filter(
            cls.is_trending == True,
            cls.expires_at > now
        ).count()
        
        avg_trend_score = session.query(func.avg(cls.trend_score)).filter(
            cls.expires_at > now
        ).scalar() or 0.0
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'trending_entries': trending_entries,
            'cache_hit_rate': round((valid_entries / max(total_entries, 1)) * 100, 2),
            'average_trend_score': round(float(avg_trend_score), 3),
            'countries_cached': session.query(cls.country).distinct().count()
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            'query': self.query,
            'country': self.country,
            'timeframe': self.timeframe,
            'trend_score': self.trend_score,
            'peak_interest': self.peak_interest,
            'average_interest': self.average_interest,
            'recent_interest': self.recent_interest,
            'is_trending': self.is_trending,
            'data_points': self.data_points,
            'validation_score': self.validation_score,
            'cross_platform_boost': self.cross_platform_boost,
            'platform_alignment': self.platform_alignment,
            'cache_hit': True,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'error': self.error_message
        }