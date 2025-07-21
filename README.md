# YouTube Trending Analyzer MVP

An LLM-powered platform that identifies genuine regional YouTube trends by distinguishing between "available in country X" vs "actually trending in country X" through intelligent country-relevance analysis using Google Gemini Flash.

## 🚀 Features

- **Real Regional Trend Analysis**: Uses LLM to analyze cultural relevance, not just regional availability
- **Multi-Country Support**: Germany 🇩🇪, USA 🇺🇸, France 🇫🇷, Japan 🇯🇵
- **MOMENTUM Algorithm**: Advanced trending score combining views/hour, engagement, and country relevance
- **Budget-Optimized**: Aggressive caching and batch processing to stay within €50/month
- **Fast Performance**: <5 second response time target

## 🏗️ Architecture

- **Backend**: Python FastAPI on Render
- **Frontend**: Next.js React (English) on Vercel
- **Database**: PostgreSQL on Render
- **Cache**: Redis on Render
- **LLM**: Google Gemini Flash for country relevance analysis
- **APIs**: YouTube Data API v3, Google Trends

## 🛠️ Tech Stack

### Backend
- FastAPI with Python 3.11+
- SQLAlchemy + Alembic for database
- Redis for caching
- Google Gemini Flash API
- YouTube Data API v3
- pytrends for Google Trends

### Frontend
- Next.js 14+ with TypeScript
- Tailwind CSS for styling
- Recharts for analytics
- Axios for API communication

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis
- YouTube Data API key
- Google Gemini API key

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your API keys
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.local.example .env.local  # Configure API URL
npm run dev
```

## 📊 API Usage

### Main Endpoint
```
GET /api/mvp/trending?query=AI&country=DE&timeframe=48h
```

**Response**:
```json
{
  "success": true,
  "query": "AI",
  "country": "DE",
  "timeframe": "48h",
  "algorithm": "MVP-LLM-Enhanced",
  "processing_time_ms": 3200,
  "results": [
    {
      "rank": 1,
      "video_id": "abc123",
      "title": "AI Revolution in Germany",
      "channel": "TechDE",
      "trending_score": 8500,
      "country_relevance_score": 0.95,
      "reasoning": "German channel, high German engagement rate, culturally relevant",
      "url": "https://youtube.com/watch?v=abc123"
    }
  ]
}
```

## 🔧 Configuration

### Environment Variables
```env
# API Keys
YOUTUBE_API_KEY=your_youtube_api_key
GEMINI_API_KEY=your_gemini_api_key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/yttrends
REDIS_URL=redis://host:port/0

# LLM Configuration
LLM_MONTHLY_BUDGET=50
LLM_BATCH_SIZE=20

# Cache Settings
CACHE_TTL_SEARCH=7200   # 2 hours
CACHE_TTL_VIDEO=86400   # 24 hours
```

## 📈 Budget Management

The system is designed to operate within a €50/month budget:
- Gemini Flash: ~€43/month (~275M tokens)
- Render services: €7/month
- Aggressive caching (2h TTL) for cost optimization
- Batch processing (20 videos per LLM call)

## 🚀 Deployment

### Backend (Render)
1. Connect GitHub repository to Render
2. Configure environment variables
3. Deploy with automatic PostgreSQL and Redis setup

### Frontend (Vercel)
1. Connect GitHub repository to Vercel
2. Configure `NEXT_PUBLIC_API_BASE_URL`
3. Deploy with automatic domain setup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Links

- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Architecture Overview](docs/ARCHITECTURE.md)