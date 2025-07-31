from pydantic import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "YouTube Trending Analyzer MVP"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/yttrends"
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Keys
    YOUTUBE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    # LLM Configuration
    LLM_PROVIDER: str = "gemini-flash"
    LLM_BATCH_SIZE: int = 20
    LLM_TIMEOUT: int = 30
    LLM_MONTHLY_BUDGET: float = 500.0  # Budget in EUR (increased for testing)
    
    # Cache Configuration (Budget-optimized)
    CACHE_TTL_SEARCH: int = 7200   # 2 hours
    CACHE_TTL_VIDEO: int = 86400   # 24 hours  
    CACHE_TTL_TRENDING: int = 3600 # 1 hour
    
    # Background Jobs
    TRENDING_CRAWL_INTERVAL: int = 2  # hours
    LLM_ANALYSIS_INTERVAL: int = 6    # hours
    
    # YouTube API Configuration - Increased for better analysis
    YOUTUBE_MAX_RESULTS: int = 200
    YOUTUBE_MAX_COMMENTS: int = 200
    
    # Supported Countries
    SUPPORTED_COUNTRIES: List[str] = ["DE", "US", "FR", "JP"]
    SUPPORTED_TIMEFRAMES: List[str] = ["24h", "48h", "7d"]
    
    # Performance Settings
    MAX_RESPONSE_TIME: float = 5.0  # seconds
    TARGET_CACHE_HIT_RATE: float = 0.70  # 70%
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()


def get_timeframe_hours(timeframe: str) -> int:
    """Convert timeframe string to hours."""
    timeframe_map = {
        "24h": 24,
        "48h": 48, 
        "7d": 168  # 7 * 24
    }
    return timeframe_map.get(timeframe, 48)


def get_country_name(country_code: str) -> str:
    """Get English country name from country code."""
    country_names = {
        "DE": "Germany",
        "US": "USA",
        "FR": "France", 
        "JP": "Japan"
    }
    return country_names.get(country_code, country_code)


def validate_country(country: str) -> bool:
    """Validate if country code is supported."""
    return country in settings.SUPPORTED_COUNTRIES


def normalize_timeframe(timeframe: str) -> str:
    """
    Normalize timeframe input to supported format.
    
    Converts user-friendly inputs to standard format:
    - "24" -> "24h"
    - "48" -> "48h" 
    - "7" -> "7d"
    - "1d" -> "24h"
    - "2d" -> "48h"
    - "1w" -> "7d"
    - "week" -> "7d"
    """
    timeframe = timeframe.lower().strip()
    
    # Direct mapping for common variations
    timeframe_map = {
        "24": "24h",
        "48": "48h", 
        "7": "7d",
        "1d": "24h",
        "2d": "48h",
        "1w": "7d",
        "week": "7d",
        "day": "24h",
        "2days": "48h"
    }
    
    # Check if it's a mapped value
    if timeframe in timeframe_map:
        return timeframe_map[timeframe]
    
    # Return as-is if already in correct format
    return timeframe


def validate_timeframe(timeframe: str) -> bool:
    """Validate if timeframe is supported (after normalization)."""
    normalized = normalize_timeframe(timeframe)
    return normalized in settings.SUPPORTED_TIMEFRAMES