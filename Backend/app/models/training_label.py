from sqlalchemy import Column, String, Integer, Boolean, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class TrainingLabel(Base):
    """Training data labels for future model improvement (low priority)."""
    
    __tablename__ = "training_labels"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to video
    video_id = Column(String(20), ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Training parameters
    country = Column(String(2), nullable=False, index=True)
    query = Column(String(255), index=True)
    
    # Training labels
    is_relevant = Column(Boolean, nullable=False, doc="Manual relevance judgment")
    relevance_score = Column(Float, doc="Manual relevance score (0.0-1.0)")
    reasoning = Column(Text, doc="Human reasoning for the label")
    
    # Metadata
    labeled_by = Column(String(50), default='admin', doc="Who created the label")
    labeled_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    
    # Relationship to video
    video = relationship("Video", backref="training_labels")
    
    # Indexes
    __table_args__ = (
        Index('idx_training_country', 'country', 'is_relevant'),
        Index('idx_video_country', 'video_id', 'country'),
        Index('idx_labeled_at', 'labeled_at'),
        Index('idx_query', 'query'),
    )
    
    def __repr__(self):
        return f"<TrainingLabel(video_id='{self.video_id}', country='{self.country}', relevant={self.is_relevant})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'country': self.country,
            'query': self.query,
            'is_relevant': self.is_relevant,
            'relevance_score': self.relevance_score,
            'reasoning': self.reasoning,
            'labeled_by': self.labeled_by,
            'labeled_at': self.labeled_at.isoformat() if self.labeled_at else None
        }
    
    @classmethod
    def get_by_country(cls, db, country: str, limit: int = 100):
        """Get training labels for a specific country."""
        return db.query(cls).filter(
            cls.country == country
        ).order_by(cls.labeled_at.desc()).limit(limit).all()
    
    @classmethod
    def get_unlabeled_videos(cls, db, country: str, limit: int = 10):
        """Get videos that need labeling for training (for future implementation)."""
        from .video import Video
        from .country_relevance import CountryRelevance
        from datetime import datetime, timezone, timedelta
        
        # Get videos from last 7 days that haven't been labeled yet
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        return db.query(Video).join(CountryRelevance).outerjoin(cls).filter(
            CountryRelevance.country == country,
            Video.upload_date >= cutoff_date,
            Video.views > 1000,
            cls.id == None  # Not yet labeled
        ).order_by(Video.views.desc()).limit(limit).all()
    
    @classmethod
    def get_accuracy_stats(cls, db, country: str):
        """Get training accuracy statistics for a country."""
        total_labels = db.query(cls).filter(cls.country == country).count()
        
        if total_labels == 0:
            return {
                'total_labels': 0,
                'relevant_count': 0,
                'irrelevant_count': 0,
                'relevance_rate': 0.0
            }
        
        relevant_count = db.query(cls).filter(
            cls.country == country,
            cls.is_relevant == True
        ).count()
        
        return {
            'total_labels': total_labels,
            'relevant_count': relevant_count,
            'irrelevant_count': total_labels - relevant_count,
            'relevance_rate': relevant_count / total_labels if total_labels > 0 else 0.0
        }
    
    @property
    def label_age_days(self) -> int:
        """Get age of training label in days."""
        if not self.labeled_at:
            return 0
            
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        age = now - self.labeled_at.replace(tzinfo=timezone.utc)
        return int(age.days)
    
    def validate_score(self) -> bool:
        """Validate that relevance score is in valid range."""
        if self.relevance_score is None:
            return True  # Score is optional
        return 0.0 <= self.relevance_score <= 1.0