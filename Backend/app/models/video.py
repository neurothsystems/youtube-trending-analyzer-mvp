from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base


class Video(Base):
    """Video metadata and cache model."""
    
    __tablename__ = "videos"
    
    # Primary key
    video_id = Column(String(20), primary_key=True, index=True)
    
    # Basic metadata
    title = Column(Text, nullable=False)
    channel_name = Column(String(255), index=True)
    channel_country = Column(String(2), index=True)
    
    # Statistics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0) 
    comments = Column(Integer, default=0)
    
    # Timestamps
    upload_date = Column(DateTime(timezone=True), index=True)
    last_updated = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Content
    duration = Column(Integer)  # Duration in seconds
    thumbnail_url = Column(Text)
    description = Column(Text)
    tags = Column(JSON)  # Store as JSON array
    
    # Additional indexes for performance
    __table_args__ = (
        Index('idx_upload_date', 'upload_date'),
        Index('idx_channel_country', 'channel_country'),
        Index('idx_views', 'views'),
        Index('idx_last_updated', 'last_updated'),
    )
    
    def __repr__(self):
        return f"<Video(video_id='{self.video_id}', title='{self.title[:50]}...', views={self.views})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'video_id': self.video_id,
            'title': self.title,
            'channel_name': self.channel_name,
            'channel_country': self.channel_country,
            'views': self.views,
            'likes': self.likes,
            'comments': self.comments,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'duration': self.duration,
            'thumbnail_url': self.thumbnail_url,
            'description': self.description,
            'tags': self.tags,
            'url': f"https://youtube.com/watch?v={self.video_id}"
        }
    
    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate (likes + comments) / views."""
        if self.views == 0:
            return 0.0
        return (self.likes + self.comments) / self.views
    
    @property
    def age_hours(self) -> float:
        """Calculate video age in hours from upload date."""
        if not self.upload_date:
            return 0.0
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        age = now - self.upload_date.replace(tzinfo=timezone.utc)
        return age.total_seconds() / 3600