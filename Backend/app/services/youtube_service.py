import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
from app.core.config import settings
from app.core.redis import CacheManager

logger = logging.getLogger(__name__)


class YouTubeService:
    """YouTube Data API v3 integration service."""
    
    def __init__(self):
        """Initialize YouTube API client."""
        if not settings.YOUTUBE_API_KEY:
            logger.error("YOUTUBE_API_KEY not configured")
            self.youtube = None
            return
            
        try:
            self.youtube = build(
                'youtube', 
                'v3', 
                developerKey=settings.YOUTUBE_API_KEY,
                cache_discovery=False
            )
            logger.info("YouTube API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API client: {e}")
            self.youtube = None
    
    def _is_available(self) -> bool:
        """Check if YouTube API is available."""
        return self.youtube is not None
    
    def search_videos(self, query: str, country: str, max_results: int = 50, 
                     published_after: datetime = None) -> List[Dict]:
        """Search for videos by query and country."""
        if not self._is_available():
            logger.error("YouTube API not available")
            return []
        
        # Set default published_after to 7 days ago if not provided
        if published_after is None:
            published_after = datetime.now(timezone.utc) - timedelta(days=7)
        
        try:
            # Format published_after to RFC3339 format
            published_after_str = published_after.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            request = self.youtube.search().list(
                part='id,snippet',
                q=query,
                type='video',
                regionCode=country,
                maxResults=min(max_results, settings.YOUTUBE_MAX_RESULTS),
                publishedAfter=published_after_str,
                order='relevance',
                videoDuration='any',
                videoEmbeddable='true'
            )
            
            response = request.execute()
            videos = []
            
            for item in response.get('items', []):
                video_data = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'channel_name': item['snippet']['channelTitle'],
                    'thumbnail_url': item['snippet']['thumbnails'].get('high', {}).get('url', ''),
                    'description': item['snippet']['description'],
                    'upload_date': self._parse_youtube_datetime(item['snippet']['publishedAt']),
                    'channel_id': item['snippet']['channelId']
                }
                videos.append(video_data)
            
            logger.info(f"Found {len(videos)} videos for query '{query}' in {country}")
            return videos
            
        except HttpError as e:
            logger.error(f"YouTube API HTTP error for query '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"YouTube API search error for query '{query}': {e}")
            return []
    
    def get_video_details(self, video_ids: List[str]) -> Dict[str, Dict]:
        """Get detailed information for multiple videos."""
        if not self._is_available():
            logger.error("YouTube API not available")
            return {}
        
        if not video_ids:
            return {}
        
        video_details = {}
        
        # YouTube API allows max 50 IDs per request
        for i in range(0, len(video_ids), 50):
            batch_ids = video_ids[i:i+50]
            
            try:
                request = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails,status',
                    id=','.join(batch_ids),
                    maxResults=50
                )
                
                response = request.execute()
                
                for item in response.get('items', []):
                    video_id = item['id']
                    snippet = item['snippet']
                    statistics = item.get('statistics', {})
                    content_details = item.get('contentDetails', {})
                    
                    video_details[video_id] = {
                        'video_id': video_id,
                        'title': snippet['title'],
                        'channel_name': snippet['channelTitle'],
                        'channel_country': snippet.get('defaultLanguage', '').upper()[:2] if snippet.get('defaultLanguage') else None,
                        'description': snippet.get('description', ''),
                        'upload_date': self._parse_youtube_datetime(snippet['publishedAt']),
                        'thumbnail_url': snippet['thumbnails'].get('high', {}).get('url', ''),
                        'views': int(statistics.get('viewCount', 0)),
                        'likes': int(statistics.get('likeCount', 0)),
                        'comments': int(statistics.get('commentCount', 0)),
                        'duration': self._parse_duration(content_details.get('duration', 'PT0S')),
                        'tags': snippet.get('tags', []),
                        'category_id': snippet.get('categoryId', ''),
                        'channel_id': snippet['channelId']
                    }
                
            except HttpError as e:
                logger.error(f"YouTube API HTTP error for video details: {e}")
            except Exception as e:
                logger.error(f"YouTube API video details error: {e}")
        
        logger.info(f"Retrieved details for {len(video_details)} videos")
        return video_details
    
    def get_trending_videos(self, country: str, max_results: int = 50) -> List[Dict]:
        """Get trending videos for a specific country."""
        if not self._is_available():
            logger.error("YouTube API not available")
            return []
        
        # Check cache first
        cached_feed = CacheManager.get_trending_feed(country)
        if cached_feed:
            logger.info(f"Retrieved trending videos for {country} from cache")
            return cached_feed
        
        try:
            request = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                chart='mostPopular',
                regionCode=country,
                maxResults=min(max_results, settings.YOUTUBE_MAX_RESULTS),
                videoCategoryId=0  # All categories
            )
            
            response = request.execute()
            trending_videos = []
            
            for idx, item in enumerate(response.get('items', []), 1):
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                content_details = item.get('contentDetails', {})
                
                video_data = {
                    'video_id': item['id'],
                    'title': snippet['title'],
                    'channel_name': snippet['channelTitle'],
                    'channel_id': snippet['channelId'],
                    'description': snippet.get('description', ''),
                    'upload_date': self._parse_youtube_datetime(snippet['publishedAt']),
                    'thumbnail_url': snippet['thumbnails'].get('high', {}).get('url', ''),
                    'views': int(statistics.get('viewCount', 0)),
                    'likes': int(statistics.get('likeCount', 0)),
                    'comments': int(statistics.get('commentCount', 0)),
                    'duration': self._parse_duration(content_details.get('duration', 'PT0S')),
                    'trending_rank': idx,
                    'category': snippet.get('categoryId', ''),
                    'tags': snippet.get('tags', [])
                }
                trending_videos.append(video_data)
            
            # Cache the results
            CacheManager.cache_trending_feed(country, trending_videos)
            
            logger.info(f"Retrieved {len(trending_videos)} trending videos for {country}")
            return trending_videos
            
        except HttpError as e:
            logger.error(f"YouTube API HTTP error for trending videos in {country}: {e}")
            return []
        except Exception as e:
            logger.error(f"YouTube API trending videos error for {country}: {e}")
            return []
    
    def get_video_comments(self, video_id: str, max_results: int = None) -> List[Dict]:
        """Get comments for a video (for geographic analysis)."""
        if not self._is_available():
            logger.error("YouTube API not available")
            return []
        
        if max_results is None:
            max_results = settings.YOUTUBE_MAX_COMMENTS
        
        try:
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_results, 100),
                order='relevance',
                textFormat='plainText'
            )
            
            response = request.execute()
            comments = []
            
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comment_data = {
                    'comment_id': item['id'],
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'like_count': comment.get('likeCount', 0),
                    'published_at': self._parse_youtube_datetime(comment['publishedAt'])
                }
                comments.append(comment_data)
            
            logger.info(f"Retrieved {len(comments)} comments for video {video_id}")
            return comments
            
        except HttpError as e:
            # Comments might be disabled
            if e.resp.status == 403:
                logger.info(f"Comments disabled for video {video_id}")
            else:
                logger.error(f"YouTube API HTTP error for comments on {video_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"YouTube API comments error for {video_id}: {e}")
            return []
    
    def _parse_youtube_datetime(self, datetime_str: str) -> datetime:
        """Parse YouTube's ISO 8601 datetime format."""
        try:
            # Remove timezone info and parse
            clean_datetime = datetime_str.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_datetime)
        except Exception as e:
            logger.error(f"Error parsing datetime '{datetime_str}': {e}")
            return datetime.now(timezone.utc)
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse YouTube's PT format duration to seconds."""
        try:
            # Parse PT format (e.g., PT4M13S, PT1H2M3S)
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration_str)
            
            if not match:
                return 0
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0) 
            seconds = int(match.group(3) or 0)
            
            return hours * 3600 + minutes * 60 + seconds
            
        except Exception as e:
            logger.error(f"Error parsing duration '{duration_str}': {e}")
            return 0
    
    def analyze_comment_geography(self, comments: List[Dict], target_country: str) -> float:
        """Analyze comment patterns for geographic relevance (simple heuristic)."""
        if not comments:
            return 0.0
        
        country_indicators = {
            'DE': ['deutsch', 'germany', 'deutschland', 'german', 'berlin', 'münchen', 'hamburg'],
            'US': ['america', 'american', 'usa', 'united states', 'english', 'dollars'],
            'FR': ['france', 'french', 'français', 'paris', 'bonjour', 'merci'],
            'JP': ['japan', 'japanese', 'tokyo', 'nihon', 'arigatou', 'konnichiwa']
        }
        
        indicators = country_indicators.get(target_country, [])
        relevant_comments = 0
        
        for comment in comments:
            text_lower = comment['text'].lower()
            if any(indicator in text_lower for indicator in indicators):
                relevant_comments += 1
        
        return relevant_comments / len(comments) if comments else 0.0
    
    def get_api_quota_info(self) -> Dict:
        """Get information about API quota usage (estimated)."""
        # This is a rough estimation since YouTube API doesn't provide quota info directly
        return {
            'estimated_daily_quota': 10000,  # Default quota
            'cost_per_search': 100,  # Search costs 100 units
            'cost_per_video_details': 1,  # Video details cost 1 unit per video
            'cost_per_trending': 1,  # Trending list costs 1 unit
            'cost_per_comments': 1,  # Comments cost 1 unit per request
            'note': 'Quota usage is estimated. Actual usage may vary.'
        }


# Create global YouTube service instance
youtube_service = YouTubeService()