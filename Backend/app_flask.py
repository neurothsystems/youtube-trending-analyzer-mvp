"""
Minimal Flask Backend for YouTube Trending Analyzer MVP
Compatible with Python 3.13 and Render deployment
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["*"])

# Configuration from environment variables
class Config:
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    REDIS_URL = os.getenv('REDIS_URL', '')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

config = Config()

# Initialize services
redis_client = None
db_connection = None

try:
    if config.REDIS_URL:
        redis_client = redis.from_url(config.REDIS_URL)
        logger.info("Redis connected successfully")
except Exception as e:
    logger.error(f"Redis connection failed: {e}")

try:
    if config.GEMINI_API_KEY:
        genai.configure(api_key=config.GEMINI_API_KEY)
        logger.info("Gemini AI configured successfully")
except Exception as e:
    logger.error(f"Gemini AI configuration failed: {e}")

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def get_youtube_trending(country: str = 'US', max_results: int = 50) -> List[Dict]:
    """Fetch YouTube trending videos"""
    try:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet,statistics',
            'chart': 'mostPopular',
            'regionCode': country,
            'maxResults': max_results,
            'key': config.YOUTUBE_API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        videos = []
        
        for item in data.get('items', []):
            video = {
                'video_id': item['id'],
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'views': int(item['statistics'].get('viewCount', 0)),
                'likes': int(item['statistics'].get('likeCount', 0)),
                'comments': int(item['statistics'].get('commentCount', 0)),
                'upload_date': item['snippet']['publishedAt'],
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'url': f"https://youtube.com/watch?v={item['id']}"
            }
            videos.append(video)
        
        return videos
    
    except Exception as e:
        logger.error(f"YouTube API error: {e}")
        return []

def analyze_country_relevance(videos: List[Dict], country: str) -> List[Dict]:
    """Analyze country relevance using Gemini AI"""
    try:
        if not config.GEMINI_API_KEY or not videos:
            return videos
        
        model = genai.GenerativeModel('gemini-pro')
        
        country_names = {
            'DE': 'Germany', 'US': 'USA', 'FR': 'France', 'JP': 'Japan'
        }
        country_name = country_names.get(country, country)
        
        # Process in batches of 5 for simplicity
        batch_size = 5
        for i in range(0, len(videos), batch_size):
            batch = videos[i:i + batch_size]
            
            # Create prompt for batch analysis
            video_list = "\n".join([
                f"{j+1}. Title: {video['title']}\n   Channel: {video['channel']}"
                for j, video in enumerate(batch)
            ])
            
            prompt = f"""Analyze these YouTube videos for relevance to {country_name}:

{video_list}

For each video, provide a relevance score (0.0-1.0) and brief reasoning. Consider:
- Language used
- Cultural references  
- Geographic content
- Target audience
- Creator location

Respond with JSON format:
[{{"video_index": 1, "relevance_score": 0.8, "reasoning": "English content targeted at US audience"}}, ...]"""

            try:
                response = model.generate_content(prompt)
                analysis = json.loads(response.text)
                
                # Apply analysis to videos
                for analysis_item in analysis:
                    video_idx = analysis_item.get('video_index', 1) - 1
                    if 0 <= video_idx < len(batch):
                        batch[video_idx]['country_relevance_score'] = analysis_item.get('relevance_score', 0.5)
                        batch[video_idx]['reasoning'] = analysis_item.get('reasoning', 'No analysis available')
                        
            except Exception as e:
                logger.error(f"LLM analysis error: {e}")
                # Set default values
                for video in batch:
                    video['country_relevance_score'] = 0.5
                    video['reasoning'] = 'Analysis unavailable'
        
        return videos
        
    except Exception as e:
        logger.error(f"Country relevance analysis error: {e}")
        return videos

def calculate_trending_score(video: Dict) -> float:
    """Calculate MOMENTUM MVP trending score"""
    try:
        views = video.get('views', 0)
        likes = video.get('likes', 0)
        comments = video.get('comments', 0)
        relevance = video.get('country_relevance_score', 0.5)
        
        # Basic engagement rate
        engagement_rate = (likes + comments) / max(views, 1) * 100
        
        # Simple trending score calculation
        base_score = (views / 1000) + (engagement_rate * 100) 
        trending_score = base_score * (0.5 + relevance)  # Apply relevance multiplier
        
        return round(trending_score, 2)
        
    except Exception as e:
        logger.error(f"Trending score calculation error: {e}")
        return 0.0

@app.route('/api/mvp/health', methods=['GET'])
def health_check():
    """System health check"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'environment': config.ENVIRONMENT,
            'checks': {
                'youtube_api': {'status': 'healthy' if config.YOUTUBE_API_KEY else 'warning'},
                'gemini_api': {'status': 'healthy' if config.GEMINI_API_KEY else 'warning'},
                'redis': {'status': 'healthy' if redis_client else 'warning'},
                'database': {'status': 'healthy' if config.DATABASE_URL else 'warning'}
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/mvp/trending', methods=['GET'])
def get_trending_analysis():
    """Main trending analysis endpoint"""
    try:
        # Get parameters
        query = request.args.get('query', 'trending')
        country = request.args.get('country', 'US')
        timeframe = request.args.get('timeframe', '48h')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Validate country
        if country not in ['DE', 'US', 'FR', 'JP']:
            return jsonify({'error': 'Unsupported country. Use: DE, US, FR, JP'}), 400
        
        start_time = datetime.utcnow()
        
        # Check cache first
        cache_key = f"trending:{country}:{timeframe}:{query}"
        cached_result = None
        
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    cached_result = json.loads(cached_data)
                    logger.info("Cache hit for trending analysis")
            except Exception as e:
                logger.error(f"Cache read error: {e}")
        
        if cached_result:
            # Return cached result
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            cached_result['metadata']['processing_time_ms'] = processing_time
            cached_result['metadata']['cache_hit'] = True
            return jsonify(cached_result)
        
        # Fresh analysis
        logger.info(f"Starting fresh analysis for {country} - {query}")
        
        # 1. Get YouTube trending videos
        videos = get_youtube_trending(country, 50)
        
        if not videos:
            return jsonify({'error': 'Failed to fetch YouTube data'}), 500
        
        # 2. Filter by query if specified
        if query and query.lower() != 'trending':
            videos = [v for v in videos if query.lower() in v['title'].lower()]
        
        # 3. Analyze country relevance with LLM
        videos = analyze_country_relevance(videos, country)
        
        # 4. Calculate trending scores
        for video in videos:
            video['trending_score'] = calculate_trending_score(video)
            video['engagement_rate'] = round(
                (video.get('likes', 0) + video.get('comments', 0)) / max(video.get('views', 1), 1) * 100, 
                2
            )
        
        # 5. Sort by trending score and limit results
        videos.sort(key=lambda x: x['trending_score'], reverse=True)
        videos = videos[:limit]
        
        # 6. Add rank
        for i, video in enumerate(videos):
            video['rank'] = i + 1
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        result = {
            'success': True,
            'query': query,
            'country': country,
            'timeframe': timeframe,
            'algorithm': 'MVP-LLM-Enhanced',
            'processing_time_ms': round(processing_time, 1),
            'results': videos,
            'metadata': {
                'total_analyzed': len(videos),
                'llm_analyzed': len(videos),
                'cache_hit': False,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Cache result for 2 hours
        if redis_client:
            try:
                redis_client.setex(cache_key, 7200, json.dumps(result))
                logger.info("Result cached successfully")
            except Exception as e:
                logger.error(f"Cache write error: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Trending analysis error: {e}")
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500

@app.route('/api/mvp/trending/feeds/<country>', methods=['GET'])
def get_trending_feeds(country):
    """Get official YouTube trending feed"""
    try:
        if country not in ['DE', 'US', 'FR', 'JP']:
            return jsonify({'error': 'Unsupported country'}), 400
        
        videos = get_youtube_trending(country, 50)
        
        country_names = {
            'DE': 'Germany', 'US': 'USA', 'FR': 'France', 'JP': 'Japan'
        }
        
        result = {
            'success': True,
            'country': country,
            'country_name': country_names.get(country, country),
            'total_videos': len(videos),
            'trending_videos': videos
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Trending feeds error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'YouTube Trending Analyzer MVP',
        'version': '1.0.0',
        'status': 'running',
        'docs': '/api/mvp/health'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)