# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube Trending Analyzer V7.0 project - an LLM-powered platform that identifies genuine regional YouTube trends by distinguishing between "available in country X" vs "actually trending in country X" through intelligent country-relevance analysis.

**Core Innovation:** Uses Gemini Flash LLM to analyze video content, channel geography, comments, and cultural context to determine true regional relevance rather than just regional availability.

**Target Countries:** Germany (🇩🇪), USA (🇺🇸), France (🇫🇷), Japan (🇯🇵)

## Project Structure

The repository follows a monorepo structure with separate backend and frontend applications:

```
/
├── Backend/          # Python FastAPI backend (not yet implemented)
├── Frontend/         # React/Next.js frontend (not yet implemented)  
├── _Input/           # Project specifications and documentation
│   └── 06 yt_trending_v7_spec.md  # Comprehensive project specification
```

**Current Status:** This appears to be a planning/specification phase repository. The actual implementation (Backend and Frontend directories) are empty and need to be created based on the detailed specification in `_Input/06 yt_trending_v7_spec.md`.

## Architecture Overview

Based on the specification document, the planned architecture includes:

### Backend Stack (Python/FastAPI on Render)
- **FastAPI** web framework
- **PostgreSQL** database for video metadata, country relevance scores, trending feeds
- **Redis** for caching (2-hour TTL for budget optimization)
- **Gemini Flash** LLM for country relevance analysis
- **YouTube Data API v3** for video collection
- **Google Trends** (pytrends) for validation

### Frontend Stack (React/Next.js on Vercel)  
- **Next.js 14+** framework
- **Tailwind CSS** for styling
- **Chart.js/Recharts** for analytics visualization
- **Axios** for API communication

### Key Services Architecture
```
Data Collection → LLM Analysis → Trend Scoring → API Response → Frontend Display
     ↓              ↓              ↓             ↓            ↓
YouTube API →  Gemini Flash → MOMENTUM V7.0 → FastAPI → React UI
```

## Development Commands

**Note:** Since this is in planning phase with no implementation yet, these are the planned commands based on the specification:

### Backend Development (when implemented)
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
alembic upgrade head

# Run tests
pytest

# Deploy to Render
git push origin main  # Auto-deploys via Render
```

### Frontend Development (when implemented)
```bash
# Install dependencies  
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Deploy to Vercel
vercel --prod
```

## Key Components to Implement

### 1. Country Processors (`backend/app/services/country_processors.py`)
Individual processors for each country that handle:
- Local search term generation
- Cultural relevance criteria for LLM prompts
- Region-specific analysis patterns

### 2. LLM Service (`backend/app/services/llm_service.py`)
Gemini Flash integration for:
- Batch country relevance analysis (20 videos per call for budget optimization)
- Search query expansion per country
- Cultural context scoring

### 3. Trending Algorithm (`backend/app/services/trending_service.py`)
MOMENTUM V7.0 algorithm combining:
- Views per hour momentum
- Engagement rate weighting  
- Country relevance multiplier (0.5-2.0x)
- Trending feed boost (+50% if in official trending)

### 4. YouTube Service (`backend/app/services/youtube_service.py`)
- Multi-region video collection
- Official trending feed crawling
- Comment analysis for geography detection

## Environment Configuration

### Required Environment Variables
```bash
# API Keys
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/yttrends
REDIS_URL=redis://host:port/0

# LLM Configuration  
LLM_PROVIDER=gemini-flash
LLM_BATCH_SIZE=20
LLM_MONTHLY_BUDGET=50

# Cache Settings (Budget-optimized)
CACHE_TTL_SEARCH=7200   # 2 hours
CACHE_TTL_VIDEO=86400   # 24 hours
```

## Database Schema

Key tables to implement:
- `videos` - Core video metadata and caching
- `country_relevance` - LLM-generated relevance scores per country  
- `trending_feeds` - Official YouTube trending data per region
- `search_cache` - Query result caching for budget optimization

## Budget Management

**Critical:** This project operates on a €50/month budget:
- Gemini Flash LLM: ~$43/month (~275M tokens available)
- Render services: $7/month
- Aggressive caching strategy (2-hour TTL) essential for staying within budget
- Batch processing (20 videos per LLM call) for cost efficiency

## API Endpoints to Implement

Main endpoint: `GET /api/v7/trending`
- Parameters: query, country (DE|US|FR|JP), timeframe (24h|48h|7d)
- Returns: Top 10 ranked videos with country relevance scores and reasoning

Supporting endpoints:
- `GET /api/v7/trending-feeds/{country}` - Current trending feeds
- `GET /api/v7/health` - System health check  
- `GET /api/v7/admin/dashboard` - Admin monitoring

## Testing Strategy

Focus on:
- LLM integration accuracy (country relevance scoring)
- Country processor logic validation
- MOMENTUM V7.0 algorithm correctness
- API response format compliance
- Cache performance and budget tracking

## Implementation Priority

1. **Core System:** FastAPI backend, database setup, YouTube API integration
2. **LLM Analysis:** Gemini Flash integration, country processors, batch processing  
3. **Frontend:** Next.js UI, API integration, result visualization
4. **Optimization:** Caching, performance tuning, budget monitoring
5. **Training System:** Manual labeling interface (low priority - future enhancement)

## Development Notes

- Empty repository currently - implementation needs to start from scratch based on specification
- All 4 countries should be implemented in parallel from the start
- Budget monitoring is critical - implement cost tracking early
- Response time target: <5 seconds end-to-end
- Cache hit rate target: >70% for budget efficiency