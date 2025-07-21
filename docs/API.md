# API Documentation - YouTube Trending Analyzer MVP

This document provides comprehensive documentation for the YouTube Trending Analyzer MVP API.

## Base URL

```
Production: https://your-backend.onrender.com
Development: http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Rate Limiting

The API implements budget-conscious rate limiting to stay within the €50/month LLM budget. Aggressive caching is used to minimize costs.

## Response Format

All API responses follow this standard format:

```json
{
  "success": boolean,
  "data": object | array,
  "error": string | null,
  "metadata": {
    "processing_time_ms": number,
    "cache_hit": boolean,
    "timestamp": "ISO-8601 datetime"
  }
}
```

## Core Endpoints

### 1. Trending Analysis

Analyze trending videos for a specific query, country, and timeframe.

**Endpoint:** `GET /api/mvp/trending`

**Parameters:**
- `query` (required): Search term (2-100 characters)
- `country` (required): Country code - `DE`, `US`, `FR`, `JP`
- `timeframe` (required): Time period - `24h`, `48h`, `7d`
- `limit` (optional): Number of results (1-50, default: 10)

**Example Request:**
```bash
curl "https://your-backend.onrender.com/api/mvp/trending?query=gaming&country=US&timeframe=48h&limit=10"
```

**Example Response:**
```json
{
  "success": true,
  "query": "gaming",
  "country": "US",
  "timeframe": "48h",
  "algorithm": "MVP-LLM-Enhanced",
  "processing_time_ms": 3245,
  "results": [
    {
      "rank": 1,
      "video_id": "abc123xyz",
      "title": "Epic Gaming Moments 2024",
      "channel": "GameMaster",
      "channel_country": "US",
      "views": 1500000,
      "views_in_timeframe": 500000,
      "likes": 45000,
      "comments": 3200,
      "trending_score": 8750.5,
      "country_relevance_score": 0.95,
      "is_in_trending_feed": true,
      "reasoning": "American gaming channel with high US audience engagement, English content, US gaming culture references",
      "url": "https://youtube.com/watch?v=abc123xyz",
      "thumbnail": "https://img.youtube.com/vi/abc123xyz/hqdefault.jpg",
      "upload_date": "2024-07-20T14:30:00Z",
      "age_hours": 18.5,
      "engagement_rate": 3.2
    }
  ],
  "metadata": {
    "total_analyzed": 127,
    "llm_analyzed": 45,
    "cache_hit": false,
    "trending_feed_matches": 3,
    "llm_cost_cents": 1.2
  }
}
```

### 2. Trending Feeds

Get official YouTube trending feed for a country.

**Endpoint:** `GET /api/mvp/trending/feeds/{country}`

**Parameters:**
- `country` (path): Country code - `DE`, `US`, `FR`, `JP`
- `fresh_only` (optional): Only return fresh data (<4h old)

**Example Request:**
```bash
curl "https://your-backend.onrender.com/api/mvp/trending/feeds/US?fresh_only=true"
```

**Example Response:**
```json
{
  "success": true,
  "country": "US",
  "country_name": "USA",
  "total_videos": 50,
  "trending_videos": [
    {
      "video_id": "xyz789abc",
      "title": "Breaking: Major Tech Announcement",
      "channel_name": "TechNews",
      "trending_rank": 1,
      "category": "News & Politics",
      "views": 2000000,
      "likes": 80000,
      "comments": 12000,
      "upload_date": "2024-07-21T10:00:00Z"
    }
  ],
  "fresh_only": true,
  "note": "Data from YouTube's official trending feed"
}
```

### 3. Search Term Expansion

Get LLM-generated search term variants for better country-specific results.

**Endpoint:** `GET /api/mvp/trending/search-terms`

**Parameters:**
- `query` (required): Original search term
- `country` (required): Target country code

**Example Request:**
```bash
curl "https://your-backend.onrender.com/api/mvp/trending/search-terms?query=music&country=DE"
```

**Example Response:**
```json
{
  "success": true,
  "original_query": "music",
  "country": "DE",
  "country_name": "Germany",
  "expanded_terms": [
    "music",
    "musik deutsch",
    "deutsche musik",
    "music germany",
    "musik deutschland"
  ],
  "total_terms": 5
}
```

## Health & Monitoring Endpoints

### 4. System Health

Check overall system health status.

**Endpoint:** `GET /api/mvp/health`

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-07-21T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection OK"
    },
    "redis": {
      "status": "healthy", 
      "message": "Redis cache OK"
    },
    "youtube_api": {
      "status": "healthy",
      "message": "YouTube API OK"
    },
    "llm_service": {
      "status": "healthy",
      "message": "LLM service OK",
      "budget_warning": false
    }
  },
  "message": "All systems operational"
}
```

### 5. Simple Health Check

Lightweight health check for load balancers.

**Endpoint:** `GET /api/mvp/health/simple`

**Example Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-07-21T12:00:00Z",
  "service": "YouTube Trending Analyzer MVP"
}
```

### 6. Readiness Probe

Kubernetes-style readiness check.

**Endpoint:** `GET /api/mvp/health/ready`

### 7. Liveness Probe

Kubernetes-style liveness check.

**Endpoint:** `GET /api/mvp/health/live`

## Analytics Endpoints

### 8. Country Analytics

Get analytics for a specific country.

**Endpoint:** `GET /api/mvp/analytics/country/{country}`

**Parameters:**
- `country` (path): Country code
- `days` (optional): Analysis period in days (1-30, default: 7)

**Example Response:**
```json
{
  "success": true,
  "country": "US",
  "country_name": "USA", 
  "analysis_period": {
    "days": 7,
    "start_date": "2024-07-14T12:00:00Z",
    "end_date": "2024-07-21T12:00:00Z"
  },
  "video_statistics": {
    "total_videos_analyzed": 1250,
    "average_relevance_score": 0.742,
    "high_relevance_count": 456,
    "high_relevance_percentage": 36.5
  },
  "trending_feed_statistics": {
    "trending_feed_entries": 350,
    "trending_matches": 125,
    "match_rate_percentage": 35.7
  },
  "llm_performance": {
    "average_confidence_score": 0.834,
    "model_used": "gemini-flash"
  },
  "popular_queries": [
    {"query": "gaming", "search_count": 45},
    {"query": "music", "search_count": 38}
  ],
  "top_videos": [
    {
      "video_id": "abc123",
      "title": "Top Gaming Video",
      "relevance_score": 0.98,
      "views": 2000000
    }
  ]
}
```

### 9. System Analytics

Get system-wide analytics and performance metrics.

**Endpoint:** `GET /api/mvp/analytics/system`

**Parameters:**
- `days` (optional): Analysis period in days (1-30, default: 7)

**Example Response:**
```json
{
  "success": true,
  "system_info": {
    "service_name": "YouTube Trending Analyzer MVP",
    "version": "1.0.0",
    "algorithm": "MVP-LLM-Enhanced",
    "environment": "production"
  },
  "api_usage": {
    "total_searches": 1843,
    "unique_queries": 456,
    "searches_per_day": 263.3
  },
  "cache_performance": {
    "status": "connected",
    "hit_rate_percentage": 74.5,
    "target_hit_rate": 70.0
  },
  "llm_usage": {
    "daily_cost_eur": 1.45,
    "monthly_cost_eur": 23.67,
    "monthly_budget_eur": 50.0,
    "budget_used_percentage": 47.3
  },
  "database_statistics": {
    "total_videos": 15678,
    "total_country_analyses": 45234,
    "recent_videos_added": 234
  }
}
```

### 10. Budget Analytics

Get detailed budget and cost information.

**Endpoint:** `GET /api/mvp/analytics/budget`

**Example Response:**
```json
{
  "success": true,
  "budget_status": "healthy",
  "budget_message": "Budget usage within normal range",
  "cost_breakdown": {
    "daily_cost_eur": 1.45,
    "monthly_cost_eur": 23.67,
    "monthly_budget_eur": 50.0,
    "budget_remaining_eur": 26.33,
    "budget_used_percentage": 47.3
  },
  "cache_optimization": {
    "current_hit_rate_percentage": 74.5,
    "target_hit_rate_percentage": 70.0,
    "cache_status": "optimal"
  },
  "recommendations": [
    {
      "type": "cache_optimization",
      "priority": "low",
      "message": "Cache performance is optimal",
      "action": "Continue monitoring"
    }
  ]
}
```

## Cache Management

### 11. Cache Statistics

Get cache performance statistics.

**Endpoint:** `GET /api/mvp/trending/cache/stats`

**Example Response:**
```json
{
  "success": true,
  "cache_stats": {
    "status": "connected",
    "hit_rate_percentage": 74.5,
    "memory_used": "15.2MB",
    "connected_clients": 3
  },
  "budget_optimization": {
    "target_hit_rate_percentage": 70,
    "current_performance": "optimal"
  }
}
```

### 12. Cache Invalidation

Invalidate cache entries (admin function).

**Endpoint:** `POST /api/mvp/trending/cache/invalidate`

**Parameters:**
- `country` (optional): Country to invalidate
- `query` (optional): Specific query to invalidate

**Example Request:**
```bash
curl -X POST "https://your-backend.onrender.com/api/mvp/trending/cache/invalidate?country=US&query=gaming"
```

## Error Handling

The API uses standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `422` - Unprocessable Entity (validation errors)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error
- `503` - Service Unavailable

**Error Response Format:**
```json
{
  "success": false,
  "error": "Unsupported country code: XX. Supported: DE, US, FR, JP",
  "detail": "Additional error details if available"
}
```

## Rate Limiting

To maintain budget constraints:

- Aggressive caching with 2-hour TTL for search results
- LLM batch processing to optimize costs
- Cache hit rate target: >70%
- Monthly budget limit: €50

## Supported Countries

- `DE` - Germany 🇩🇪
- `US` - USA 🇺🇸  
- `FR` - France 🇫🇷
- `JP` - Japan 🇯🇵

## Supported Timeframes

- `24h` - Last 24 hours
- `48h` - Last 48 hours
- `7d` - Last 7 days

## Response Time Targets

- Target: <5 seconds for trending analysis
- Typical: 2-4 seconds with cache hits
- Fresh analysis: 3-8 seconds depending on LLM processing

## Examples & Testing

### cURL Examples

```bash
# Basic trending search
curl "https://your-backend.onrender.com/api/mvp/trending?query=AI&country=DE&timeframe=24h"

# Get trending feeds
curl "https://your-backend.onrender.com/api/mvp/trending/feeds/US"

# Check system health
curl "https://your-backend.onrender.com/api/mvp/health"

# Get system analytics
curl "https://your-backend.onrender.com/api/mvp/analytics/system?days=7"
```

### JavaScript/Axios Examples

```javascript
// Trending analysis
const response = await axios.get('/api/mvp/trending', {
  params: {
    query: 'music',
    country: 'US',
    timeframe: '48h',
    limit: 10
  }
});

// Health check
const health = await axios.get('/api/mvp/health');
```

## WebSocket Support

Currently not supported. All endpoints use REST HTTP.

## API Versioning

The API is versioned using URL path versioning:
- Current version: `v1` (represented as `mvp` in URLs)
- Future versions will use `/api/v2/`, `/api/v3/`, etc.

## CORS Policy

Cross-Origin Resource Sharing (CORS) is enabled for:
- Development: `localhost:3000`
- Production: Configured frontend domains
- All origins during development (when `DEBUG=true`)

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:
```
https://your-backend.onrender.com/docs
```

Alternative ReDoc documentation:
```
https://your-backend.onrender.com/redoc
```