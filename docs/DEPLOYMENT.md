# Deployment Guide - YouTube Trending Analyzer MVP

This guide provides step-by-step instructions for deploying the YouTube Trending Analyzer MVP to production using Render (backend) and Vercel (frontend).

## 📋 Prerequisites

- [GitHub](https://github.com) account
- [Render](https://render.com) account (for backend + database)
- [Vercel](https://vercel.com) account (for frontend)
- YouTube Data API v3 key
- Google Gemini API key

## 🔑 API Keys Setup

### 1. YouTube Data API v3 Key

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3:
   - Go to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Restrict the key to YouTube Data API v3
   - Note down the API key

### 2. Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Note down the API key

## 🏗️ Backend Deployment (Render)

### Option A: Blueprint Deployment (Recommended)

1. Fork/clone this repository to your GitHub account
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Select the repository containing this project
6. Render will detect the `render.yaml` file automatically
7. Configure the required environment variables:
   - `YOUTUBE_API_KEY`: Your YouTube API key
   - `GEMINI_API_KEY`: Your Gemini API key
8. Deploy the blueprint

### Option B: Manual Service Creation

1. **Create PostgreSQL Database:**
   - Go to Render Dashboard → "New" → "PostgreSQL"
   - Name: `youtube-trending-db`
   - Plan: Starter (free tier)
   - Create database and note the connection URL

2. **Create Redis Instance:**
   - Go to Render Dashboard → "New" → "Redis"
   - Name: `youtube-trending-cache`
   - Plan: Starter (free tier)
   - Create instance and note the connection URL

3. **Create Web Service:**
   - Go to Render Dashboard → "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `youtube-trending-analyzer-api`
     - **Runtime**: Python 3
     - **Build Command**: `cd backend && pip install -r requirements.txt`
     - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Starter

4. **Environment Variables:**
   Set these in the Render dashboard:

   ```bash
   # Application
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=<generate-random-secret-key>
   
   # Database (from your PostgreSQL instance)
   DATABASE_URL=<your-postgresql-connection-string>
   
   # Redis (from your Redis instance)
   REDIS_URL=<your-redis-connection-string>
   
   # API Keys
   YOUTUBE_API_KEY=<your-youtube-api-key>
   GEMINI_API_KEY=<your-gemini-api-key>
   
   # LLM Configuration
   LLM_PROVIDER=gemini-flash
   LLM_BATCH_SIZE=20
   LLM_MONTHLY_BUDGET=50.0
   
   # Cache Settings (Budget Optimized)
   CACHE_TTL_SEARCH=7200
   CACHE_TTL_VIDEO=86400
   CACHE_TTL_TRENDING=3600
   ```

5. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Note your backend URL: `https://your-service-name.onrender.com`

## 🌐 Frontend Deployment (Vercel)

### Step 1: Update Configuration

1. **Update vercel.json:**
   Replace the placeholder URL with your actual Render backend URL:
   
   ```json
   {
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "https://YOUR-ACTUAL-BACKEND.onrender.com/api/$1"
       }
     ],
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://YOUR-ACTUAL-BACKEND.onrender.com/api/:path*"
       }
     ]
   }
   ```

### Step 2: Deploy to Vercel

1. **Connect Repository:**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Project:**
   - Framework Preset: Next.js (auto-detected)
   - Root Directory: `frontend`
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

3. **Environment Variables:**
   Set these in Vercel project settings:
   
   ```bash
   NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
   NEXT_PUBLIC_ENVIRONMENT=production
   NEXT_PUBLIC_APP_NAME=YouTube Trending Analyzer MVP
   NEXT_PUBLIC_APP_VERSION=1.0.0
   ```

4. **Deploy:**
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Note your frontend URL: `https://your-project.vercel.app`

## 🔧 Post-Deployment Configuration

### 1. CORS Setup

Update your backend environment variables to include the frontend domain:

```bash
ALLOWED_HOSTS=your-backend.onrender.com,your-frontend.vercel.app,localhost
```

### 2. Test Health Endpoints

Verify your backend is working:

```bash
curl https://your-backend.onrender.com/api/mvp/health
```

### 3. Test Full Integration

1. Open your frontend URL
2. Try a sample search (e.g., "music", "US", "48h")
3. Verify results are displayed correctly

## 📊 Monitoring & Maintenance

### Health Checks

- **Backend Health**: `https://your-backend.onrender.com/api/mvp/health`
- **System Metrics**: `https://your-backend.onrender.com/api/mvp/analytics/system`
- **Budget Status**: `https://your-backend.onrender.com/api/mvp/analytics/budget`

### Budget Monitoring

Monitor your LLM costs regularly:

1. Check the analytics endpoint for current usage
2. Set up alerts in your monitoring system
3. Adjust cache TTL settings if costs exceed budget

### Performance Optimization

1. **Cache Hit Rate**: Monitor and optimize for >70% hit rate
2. **Response Times**: Keep under 5 seconds target
3. **Database Performance**: Monitor query times and optimize indexes

## 🚨 Troubleshooting

### Common Issues

**1. Environment Variables Not Loading:**
- Verify all required environment variables are set
- Check for typos in variable names
- Restart services after changing environment variables

**2. CORS Errors:**
- Verify ALLOWED_HOSTS includes your frontend domain
- Check vercel.json configuration
- Ensure API proxy routes are correct

**3. Database Connection Issues:**
- Verify DATABASE_URL is correct
- Check if database instance is running
- Run database migrations if needed

**4. API Key Issues:**
- Verify API keys are valid and not expired
- Check API quotas and usage limits
- Ensure API keys have proper permissions

**5. LLM Budget Exceeded:**
- Check current usage at `/api/mvp/analytics/budget`
- Increase cache TTL to reduce API calls
- Implement rate limiting if needed

### Logs and Debugging

**Render Logs:**
- Go to your service dashboard
- Click "Logs" tab to view real-time logs
- Look for Python errors and API failures

**Vercel Logs:**
- Go to your project dashboard
- Check "Functions" tab for runtime logs
- Monitor build logs for deployment issues

## 🔄 Updates and Maintenance

### Automatic Deployments

Both services are configured for automatic deployment:
- **Render**: Deploys on git push to main branch
- **Vercel**: Deploys on git push to main branch

### Manual Updates

**Backend Updates:**
1. Push changes to GitHub
2. Render will auto-deploy
3. Monitor logs for successful deployment

**Frontend Updates:**
1. Push changes to GitHub
2. Vercel will auto-deploy
3. Verify changes in production

### Database Migrations

When database schema changes:

```bash
# Run migrations manually in Render shell
cd backend
alembic upgrade head
```

## 💰 Cost Management

### Free Tier Limits

**Render Free Tier:**
- 750 hours/month web service uptime
- 1GB RAM, shared CPU
- PostgreSQL: 1GB storage
- Redis: 25MB storage

**Vercel Free Tier:**
- 100GB bandwidth/month
- Unlimited static deployments

### Upgrading Plans

When you exceed free tier limits:

**Render Starter Plan (~$7/month):**
- Better performance and uptime
- More database storage

**Budget Monitoring:**
- Monitor LLM costs daily
- Target: <€50/month total cost
- Optimize caching to reduce API calls

## 📞 Support

For deployment issues:
- Check this documentation first
- Review service logs for errors
- Contact Render/Vercel support for platform issues
- Open GitHub issues for application bugs