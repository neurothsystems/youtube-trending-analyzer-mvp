from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TrendingFeed(Base):
    """Official YouTube trending feeds model."""
    
    __tablename__ = "trending_feeds"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to video
    video_id = Column(String(20), ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Trending metadata
    country = Column(String(2), nullable=False, index=True)
    trending_rank = Column(Integer, doc="Position in trending list (1-50)")
    category = Column(String(50), doc="YouTube category (Music, Gaming, etc.)")
    
    # Timestamp
    captured_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    
    # Relationship to video
    video = relationship("Video", backref="trending_feeds")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_country_captured', 'country', 'captured_at'),
        Index('idx_video_trending', 'video_id', 'trending_rank'),
        Index('idx_country_rank_captured', 'country', 'trending_rank', 'captured_at'),
    )
    
    def __repr__(self):
        return f"<TrendingFeed(video_id='{self.video_id}', country='{self.country}', rank={self.trending_rank})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'country': self.country,
            'trending_rank': self.trending_rank,
            'category': self.category,
            'captured_at': self.captured_at.isoformat() if self.captured_at else None
        }
    
    @classmethod
    def get_current_trending(cls, db, country: str, hours: int = 4):
        """Get current trending videos for a country (within specified hours)."""
        from datetime import datetime, timezone, timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return db.query(cls).filter(
            cls.country == country,
            cls.captured_at >= cutoff_time
        ).order_by(cls.trending_rank.asc()).all()
    
    @classmethod
    def get_latest_by_country(cls, db, country: str, limit: int = 50):
        """Get latest trending feed for a country."""
        return db.query(cls).filter(
            cls.country == country
        ).order_by(cls.captured_at.desc()).limit(limit).all()
    
    @classmethod
    def is_video_trending(cls, db, video_id: str, country: str, hours: int = 4) -> bool:
        """Check if video is currently in trending feed."""
        from datetime import datetime, timezone, timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        result = db.query(cls).filter(
            cls.video_id == video_id,
            cls.country == country,
            cls.captured_at >= cutoff_time
        ).first()
        
        return result is not None
    
    @property
    def age_hours(self) -> float:
        """Get age of trending entry in hours."""
        if not self.captured_at:
            return 0.0
            
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        age = now - self.captured_at.replace(tzinfo=timezone.utc)
        return age.total_seconds() / 3600
    
    @property
    def is_fresh(self) -> bool:
        """Check if trending entry is fresh (< 4 hours old)."""
        return self.age_hours < 4.0