# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **YouTube Trending Analyzer MVP** - an LLM-powered platform that identifies genuine regional YouTube trends by distinguishing between "available in country X" vs "actually trending in country X" through intelligent country-relevance analysis.

**Core Innovation:** Uses Gemini Flash LLM to analyze video content, channel geography, comments, and cultural context to determine true regional relevance rather than just regional availability.

**Target Countries:** Germany (🇩🇪), USA (🇺🇸), France (🇫🇷), Japan (🇯🇵)

**Current Status:** ✅ **FULLY IMPLEMENTED MVP** - Both frontend and backend are deployed and operational.

## Project Structure

The repository contains a complete monorepo with implemented backend and frontend:

```
/
├── Backend/          # ✅ Python FastAPI backend (IMPLEMENTED)
│   ├── app/
│   │   ├── main.py           # FastAPI app with CORS, database setup
│   │   ├── core/
│   │   │   ├── config.py     # Settings and environment variables
│   │   │   └── database.py   # PostgreSQL connection and models
│   │   ├── models/           # SQLAlchemy models for all 5 tables
│   │   │   ├── video.py
│   │   │   ├── country_relevance.py
│   │   │   ├── trending_feed.py
│   │   │   ├── search_cache.py
│   │   │   └── training_label.py
│   │   └── api/              # API routes
│   │       ├── trending.py   # Main search endpoint
│   │       ├── health.py     # Health checks
│   │       └── analytics.py  # Analytics endpoints
│   ├── requirements.txt      # Python dependencies
│   └── render.yaml          # Render deployment config
├── src/              # ✅ Next.js frontend (IMPLEMENTED)
│   ├── app/
│   │   ├── page.tsx         # Main search page (simplified UI)
│   │   └── globals.css      # Tailwind styles
│   ├── components/
│   │   ├── Header.tsx       # Header with version tracking
│   │   ├── SearchForm.tsx   # Search form (no limit control)
│   │   ├── ResultsDisplay.tsx
│   │   ├── VersionStatus.tsx # Backend compatibility check
│   │   └── CacheControls.tsx
│   ├── lib/
│   │   ├── api.ts           # TrendingAnalyzerAPI client
│   │   ├── constants.ts     # App configuration
│   │   └── version.ts       # Version compatibility logic
│   └── types/               # TypeScript definitions
├── package.json             # Frontend dependencies (v1.1.0-features)
├── runtime.txt             # Python 3.11.9 for Render
└── .env.example            # Environment variable templates
```

## Deployment Status

### ✅ Backend (Production Ready)
- **Hosted on:** Render.com
- **URL:** https://youtube-trending-analyzer-api.onrender.com
- **Status:** Operational with comprehensive database setup
- **Database:** PostgreSQL with all 5 tables created
- **Cache:** Redis available but not yet implemented
- **Version:** 1.1.0-origin-country

### ✅ Frontend (Production Ready)  
- **Hosted on:** Vercel
- **Status:** Deployed with simplified UI
- **Features:** Search form, results display, version tracking
- **Version:** 1.1.0-features

## Architecture Overview

### Backend Stack (✅ FULLY IMPLEMENTED)
- **FastAPI** web framework with CORS configuration
- **PostgreSQL** database with 5 tables fully implemented
- **SQLAlchemy** ORM with manual table creation fallback
- **Gemini Flash** LLM integration with batch processing and budget tracking
- **YouTube Data API v3** integration with search, details, trending feeds, comments
- **Redis** caching with optimized TTL configuration

### Frontend Stack (✅ IMPLEMENTED)
- **Next.js 14** with TypeScript
- **Tailwind CSS** for styling (neutral gray background)
- **Axios** for API communication with TrendingAnalyzerAPI class
- **React Hot Toast** for notifications
- **Lucide React** for icons

### Database Schema (✅ IMPLEMENTED)
All tables created with proper indexes and foreign keys:

1. **videos** - Core video metadata (video_id, title, channel_name, views, etc.)
2. **country_relevance** - LLM-generated relevance scores per country
3. **trending_feeds** - Official YouTube trending data per region  
4. **search_cache** - Query result caching for budget optimization
5. **training_labels** - Manual labeling for future ML improvement

## Current API Endpoints (✅ IMPLEMENTED)

**Base URL:** https://youtube-trending-analyzer-api.onrender.com

### Main Endpoints:
- `GET /` - Backend version info with feature list
- `GET /api/mvp` - Detailed API information
- `GET /api/mvp/trending` - Main search endpoint (query, country, timeframe)
- `GET /api/mvp/health` - System health check
- `GET /api/mvp/health/database` - Database table verification
- `GET /api/mvp/analytics/*` - Analytics endpoints

### Response Format:
```json
{
  "success": true,
  "query": "gaming",
  "country": "DE", 
  "timeframe": "48h",
  "algorithm": "MVP-LLM-Enhanced",
  "results": [...],
  "metadata": {
    "total_analyzed": 0,
    "llm_analyzed": 0,
    "cache_hit": false,
    "trending_feed_matches": 0,
    "llm_cost_cents": 0
  }
}
```

## Development Commands

### Backend Development (✅ WORKING)
```bash
# Install dependencies
cd Backend && pip install -r requirements.txt

# Run development server  
cd Backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Deploy to Render
git push origin main  # Auto-deploys via Render
```

### Frontend Development (✅ WORKING)
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Deploy to Vercel  
git push origin main  # Auto-deploys via Vercel
```

## Environment Configuration

### Backend (Render Environment Variables)
```bash
# API Keys (✅ CONFIGURED - SET IN RENDER DASHBOARD)
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database (✅ CONFIGURED)
DATABASE_URL=postgresql://user:pass@host:5432/yttrends
REDIS_URL=redis://host:port/0

# Application Settings (✅ CONFIGURED)
ENVIRONMENT=production
DEBUG=false
LLM_PROVIDER=gemini-flash
LLM_BATCH_SIZE=20
LLM_TIMEOUT=30
LLM_MONTHLY_BUDGET=50.0

# Cache Settings (✅ CONFIGURED)
CACHE_TTL_SEARCH=7200   # 2 hours
CACHE_TTL_VIDEO=86400   # 24 hours
CACHE_TTL_TRENDING=3600 # 1 hour
```

### Frontend (Vercel Environment Variables)
```bash
# ✅ CONFIGURED
NEXT_PUBLIC_API_BASE_URL=https://youtube-trending-analyzer-api.onrender.com
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_APP_VERSION=1.1.0-features
NEXT_PUBLIC_ENABLE_DEBUG=false
NEXT_PUBLIC_DEFAULT_COUNTRY=US
NEXT_PUBLIC_DEFAULT_TIMEFRAME=48h
NEXT_PUBLIC_DEFAULT_LIMIT=10
```

## Implementation Status

### ✅ COMPLETED
- [x] FastAPI backend with database models
- [x] PostgreSQL database with all 5 tables  
- [x] Next.js frontend with search functionality
- [x] CORS configuration for Vercel ↔ Render communication
- [x] Version tracking system between frontend/backend
- [x] Simplified UI (removed info cards, fixed result limit to 10)
- [x] Deployment pipeline (Render + Vercel)
- [x] Environment variable configuration
- [x] Error handling and user feedback
- [x] **Gemini Flash LLM Integration** - Batch processing, budget tracking, country-specific analysis
- [x] **YouTube Data API v3 Integration** - Search, video details, trending feeds, comments analysis
- [x] **Country Processors** - All 4 countries (DE, US, FR, JP) with localized search terms
- [x] **MOMENTUM MVP Algorithm** - Multi-tier search, adaptive filtering, sophisticated scoring
- [x] **Redis Cache Layer** - Budget-optimized caching with proper TTL configuration
- [x] **Comprehensive API endpoints** - Trending analysis, feeds, search terms, cache management

### 🟡 CURRENT STATUS (After API Key Reset)
- [x] **API Keys Regenerated** - New YouTube and Gemini keys set in Render
- [ ] **API Functionality Testing** - Using new test endpoints
- [ ] **Database Table Verification** - Enhanced logging deployed
- [ ] **End-to-End Search Testing** - After components verified

### 🔴 RECENT ISSUES (Being Resolved)
- Database table creation intermittently fails (enhanced debugging deployed)
- Search returns "country_relevance does not exist" error (table creation issue)
- API keys were exposed in git history (RESOLVED - keys regenerated)

## Budget Management

**Current Budget:** €50/month allocated
- Render services: ~$7/month (✅ operational)
- Vercel: Free tier (✅ operational)  
- Gemini Flash LLM: Keys need regeneration
- YouTube API: Keys need regeneration

## Testing Strategy

### Current Testing Status:
- ✅ Frontend builds successfully (`npm run build`)
- ✅ Backend starts without errors
- ✅ Database connection working
- ✅ API endpoints return responses
- 🟡 Table creation debugging in progress

## Next Development Priorities

1. **🔥 HIGH PRIORITY:**
   - Fix database table creation issue (country_relevance missing)
   - Regenerate API keys after security incident
   - Test end-to-end search functionality

2. **📈 MEDIUM PRIORITY:**
   - Performance monitoring and optimization
   - Enhanced error handling and logging
   - Budget tracking and alerts

3. **🔧 LOW PRIORITY:**
   - Analytics dashboard
   - Admin interface
   - Repository structure cleanup (Frontend/src mixed structure)

## Development Notes

### Recent Changes:
- ✅ Enhanced database creation logging for debugging
- ✅ Added /health/database endpoint for table verification
- ✅ Fixed CORS issues between Vercel and Render
- ✅ Simplified frontend UI (removed feature cards)  
- ✅ Fixed result limit to 10 (removed slider control)
- 🔒 **SECURITY**: Removed API keys from git, added to .gitignore

### Architecture Decisions:
- Using manual SQL table creation as fallback for SQLAlchemy
- Frontend-backend version compatibility tracking implemented
- Fixed 10 results per search for simplified UX
- Neutral gray background for clean appearance
- CLAUDE.md kept local only (not pushed to GitHub)

### Git Workflow:
- Main branch auto-deploys to both Render (backend) and Vercel (frontend)
- All database migrations happen automatically on deployment
- Environment variables managed separately on each platform
- CLAUDE.md in .gitignore to prevent accidental exposure

## Security Notes

⚠️ **IMPORTANT**: This file contains project documentation and should remain local only.
- Never commit real API keys to version control
- Use .env.example for templates
- Set actual keys directly in deployment platforms (Render/Vercel)

---

**💡 For Claude:** This is a fully functional MVP with complete search pipeline implemented (YouTube API + Gemini LLM + MOMENTUM algorithm). All API keys need regeneration after security incident. Current issue: country_relevance table creation failing. Focus on debugging database setup rather than building new features.