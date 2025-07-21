from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class CountryRelevance(Base):
    """LLM-generated country relevance scores model."""
    
    __tablename__ = "country_relevance"
    
    # Composite primary key
    video_id = Column(String(20), ForeignKey('videos.video_id', ondelete='CASCADE'), primary_key=True)
    country = Column(String(2), primary_key=True, index=True)
    
    # LLM analysis results
    relevance_score = Column(
        Float, 
        nullable=False,
        doc="Country relevance score between 0.0 and 1.0"
    )
    reasoning = Column(Text, doc="LLM reasoning for the relevance score")
    confidence_score = Column(Float, doc="Confidence in the analysis")
    
    # Metadata
    analyzed_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    llm_model = Column(String(50), default='gemini-flash')
    
    # Relationship to video
    video = relationship("Video", backref="country_relevances")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint('relevance_score >= 0 AND relevance_score <= 1', name='check_relevance_score_range'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_score_range'), 
        Index('idx_country_score', 'country', 'relevance_score'),
        Index('idx_analyzed_at', 'analyzed_at'),
        Index('idx_video_country', 'video_id', 'country'),
    )
    
    def __repr__(self):
        return f"<CountryRelevance(video_id='{self.video_id}', country='{self.country}', score={self.relevance_score:.3f})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'video_id': self.video_id,
            'country': self.country,
            'relevance_score': self.relevance_score,
            'reasoning': self.reasoning,
            'confidence_score': self.confidence_score,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
            'llm_model': self.llm_model
        }
    
    @classmethod
    def get_by_country(cls, db, country: str, min_score: float = 0.0, limit: int = 100):
        """Get top relevance scores for a country."""
        return db.query(cls).filter(
            cls.country == country,
            cls.relevance_score >= min_score
        ).order_by(cls.relevance_score.desc()).limit(limit).all()
    
    @classmethod 
    def get_by_video(cls, db, video_id: str):
        """Get all country relevance scores for a video."""
        return db.query(cls).filter(cls.video_id == video_id).all()
    
    @property
    def relevance_percentage(self) -> int:
        """Get relevance score as percentage (0-100)."""
        return int(self.relevance_score * 100)
    
    @property
    def relevance_category(self) -> str:
        """Categorize relevance score."""
        if self.relevance_score >= 0.8:
            return "High"
        elif self.relevance_score >= 0.6:
            return "Medium" 
        elif self.relevance_score >= 0.3:
            return "Low"
        else:
            return "Very Low"