from sqlalchemy import Column, Integer, String, DateTime, Decimal, UUID
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.core.database import Base
from datetime import datetime, timezone
import uuid


class LLMUsageLog(Base):
    """Log table for tracking LLM usage and costs."""
    
    __tablename__ = "llm_usage_log"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(PG_UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    model_name = Column(String(50), nullable=False, index=True)
    
    # Token counts
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    
    # Costs
    cost_usd = Column(Decimal(10, 6), nullable=False)
    cost_eur = Column(Decimal(10, 6), nullable=True)
    exchange_rate = Column(Decimal(8, 4), nullable=True)
    
    # Context
    country = Column(String(2), nullable=True, index=True)
    query = Column(String(255), nullable=True)
    video_count = Column(Integer, nullable=True)
    
    # Metadata
    processing_time_ms = Column(Integer, nullable=True)
    cache_hit = Column(String(10), nullable=True)  # 'true', 'false', 'partial'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f"<LLMUsageLog(id={self.id}, model={self.model_name}, cost_usd={self.cost_usd}, tokens_in={self.input_tokens}, tokens_out={self.output_tokens})>"