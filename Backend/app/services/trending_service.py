import logging
import math
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.core.config import settings, get_timeframe_hours
from app.models.video import Video
from app.models.country_relevance import CountryRelevance
from app.models.trending_feed import TrendingFeed
from app.services.youtube_service import youtube_service
from app.services.llm_service import llm_service
from app.services.google_trends_service import google_trends_service
from app.services.country_processors import CountryProcessorFactory
from app.services.google_trends_search_enhancer import google_trends_search_enhancer
from app.core.redis import CacheManager

logger = logging.getLogger(__name__)


class TrendingService:
    """MOMENTUM MVP trending algorithm and analysis service."""
    
    def __init__(self):
        """Initialize trending service."""
        self.algorithm_version = "MVP-LLM-GoogleTrends-SearchEnhanced"
    
    def analyze_trending_videos(self, query: str, country: str, timeframe: str, 
                               db: Session, limit: int = 10) -> Dict:
        """Main method to analyze trending videos for a query/country/timeframe."""
        start_time = datetime.now()
        
        # Validate inputs
        if not self._validate_inputs(query, country, timeframe):
            raise ValueError("Invalid input parameters")
        
        # Check cache first
        cached_result = CacheManager.get_trending_results(query, country, timeframe)
        if cached_result:
            logger.info(f"Retrieved trending analysis from cache for '{query}' in {country}")
            return cached_result
        
        try:
            # Step 1: Collect videos from multiple sources with enhanced search
            videos, transparency_data = self._collect_videos(query, country, timeframe, db)
            
            if not videos:
                return self._empty_result(query, country, timeframe, "No videos found")
            
            # Step 2: Get Google Trends cross-platform validation
            google_trends_data = self._get_google_trends_analysis(query, country, timeframe)
            
            # Step 3: Get LLM country relevance analysis (batch processing)
            llm_results = self._get_country_relevance_analysis(videos, country, db, query)
            
            # Step 4: Calculate trending scores using MOMENTUM MVP algorithm with Google Trends
            scored_videos = self._calculate_trending_scores(videos, llm_results, country, timeframe, db, google_trends_data)
            
            # Step 5: Apply adaptive filtering and guarantee minimum results
            filtered_videos = self._apply_adaptive_filtering(scored_videos, limit, query, country, timeframe, db)
            
            # Step 6: Rank and format results
            final_results = self._rank_and_format_results(filtered_videos, limit)
            
            # Step 7: Prepare response with metadata
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = {
                "success": True,
                "query": query,
                "country": country,
                "timeframe": timeframe,
                "algorithm": self.algorithm_version,
                "processing_time_ms": round(processing_time),
                "results": final_results,
                "metadata": {
                    "total_analyzed": len(videos),
                    "llm_analyzed": len(llm_results),
                    "cache_hit": False,
                    "trending_feed_matches": self._count_trending_matches(final_results),
                    "llm_cost_cents": round(llm_service.daily_cost * 100, 2) if llm_service else 0,
                    "google_trends": google_trends_data,
                    "search_terms_used": transparency_data.get('search_terms_used', {}),
                    "collection_stats": transparency_data.get('collection_stats', {})
                }
            }
            
            # Cache the results
            CacheManager.cache_trending_results(query, country, timeframe, result)
            
            logger.info(f"Completed trending analysis for '{query}' in {country}. "
                       f"Found {len(final_results)} results in {processing_time:.0f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in trending analysis: {e}")
            return self._error_result(query, country, timeframe, str(e))
    
    def _validate_inputs(self, query: str, country: str, timeframe: str) -> bool:
        """Validate input parameters."""
        if not query or len(query.strip()) < 2:
            return False
        
        if country not in settings.SUPPORTED_COUNTRIES:
            return False
            
        if timeframe not in settings.SUPPORTED_TIMEFRAMES:
            return False
            
        return True
    
    def _collect_videos(self, query: str, country: str, timeframe: str, db: Session) -> tuple[List[Dict], Dict]:
        """Collect videos from multiple sources with multi-tier search strategy."""
        all_videos = []
        target_video_count = 100  # Target more videos for better LLM analysis
        
        # Initialize collection stats
        collection_stats = {
            'videos_from_search': 0,
            'videos_from_trending_feed': 0,
            'total_collected': 0,
            'duplicates_removed': 0
        }
        search_terms_used = {
            'tier_1_terms': [],
            'tier_2_terms': [],
            'tier_3_terms': [],
            'total_search_terms': 0
        }
        
        try:
            # Get country processor for search term expansion
            processor = CountryProcessorFactory.get_processor(country)
            timeframe_hours = get_timeframe_hours(timeframe)
            published_after = datetime.now(timezone.utc) - timedelta(hours=timeframe_hours)
            
            # Enhanced search strategy using Google Trends
            enhanced_search_metadata = google_trends_search_enhancer.get_search_terms_with_metadata(query, country, timeframe)
            enhanced_terms = enhanced_search_metadata['search_terms']
            
            # Fallback to country processors for additional terms if needed
            tier_2_terms = processor.get_category_terms(query)[:3]
            tier_3_terms = processor.get_generic_trending_terms()[:2]
            
            search_tiers = [enhanced_terms[:7], tier_2_terms, tier_3_terms]
            
            # Store search terms for transparency
            search_terms_used['tier_1_terms'] = enhanced_terms[:7]
            search_terms_used['tier_2_terms'] = tier_2_terms
            search_terms_used['tier_3_terms'] = tier_3_terms
            search_terms_used['total_search_terms'] = len(enhanced_terms[:7]) + len(tier_2_terms) + len(tier_3_terms)
            search_terms_used['google_trends_enhanced'] = True
            search_terms_used['enhanced_search_metadata'] = enhanced_search_metadata
            
            videos_collected = 0
            
            for tier_idx, search_terms in enumerate(search_tiers):
                if videos_collected >= target_video_count:
                    break
                    
                tier_name = "Google Trends Enhanced" if tier_idx == 0 else f"Tier {tier_idx + 1}"
                logger.info(f"{tier_name}: Searching with {len(search_terms)} terms")
                
                for search_term in search_terms:
                    if videos_collected >= target_video_count:
                        break
                    
                    # Increase results per term based on tier
                    max_results = 30 if tier_idx == 0 else (25 if tier_idx == 1 else 20)
                    
                    videos = youtube_service.search_videos(
                        search_term, 
                        country, 
                        max_results=max_results,
                        published_after=published_after
                    )
                    
                    all_videos.extend(videos)
                    videos_collected += len(videos)
                    collection_stats['videos_from_search'] += len(videos)
                    
                    logger.info(f"  '{search_term}': {len(videos)} videos (total: {videos_collected})")
            
            # Always include trending feed videos for context
            trending_videos = youtube_service.get_trending_videos(country, max_results=50)
            
            # Filter trending videos by timeframe
            filtered_trending = []
            for video in trending_videos:
                if video.get('upload_date'):
                    upload_date = video['upload_date']
                    if isinstance(upload_date, str):
                        upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                    
                    if upload_date >= published_after:
                        filtered_trending.append(video)
            
            all_videos.extend(filtered_trending)
            collection_stats['videos_from_trending_feed'] = len(filtered_trending)
            
            # Remove duplicates and prioritize variety
            unique_videos = {}
            duplicates_count = 0
            for video in all_videos:
                video_id = video.get('video_id')
                if video_id and video_id not in unique_videos:
                    unique_videos[video_id] = video
                else:
                    duplicates_count += 1
            
            collection_stats['duplicates_removed'] = duplicates_count
            collection_stats['total_collected'] = len(unique_videos)
            
            # Increase video limit for better LLM analysis
            video_ids = list(unique_videos.keys())[:150]  # Increased from 50 to 150
            
            # Process in batches to respect API limits
            detailed_videos = {}
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                batch_details = youtube_service.get_video_details(batch_ids)
                detailed_videos.update(batch_details)
            
            # Merge detailed info
            final_videos = []
            for video_id, video_data in detailed_videos.items():
                # Add trending feed status
                is_trending = any(v.get('video_id') == video_id for v in filtered_trending)
                video_data['is_in_trending_feed'] = is_trending
                final_videos.append(video_data)
            
            logger.info(f"Collected {len(final_videos)} videos for analysis (target: {target_video_count})")
            
            # Prepare transparency data
            transparency_data = {
                'search_terms_used': search_terms_used,
                'collection_stats': collection_stats
            }
            
            return final_videos, transparency_data
            
        except Exception as e:
            logger.error(f"Error collecting videos: {e}")
            return [], {'search_terms_used': search_terms_used, 'collection_stats': collection_stats}
    
    def _get_country_relevance_analysis(self, videos: List[Dict], country: str, 
                                       db: Session, query: str = None) -> Dict[str, Dict]:
        """Get country relevance analysis from LLM or database."""
        video_ids = [v['video_id'] for v in videos]
        
        # Check database first for existing analysis
        existing_analysis = db.query(CountryRelevance).filter(
            CountryRelevance.video_id.in_(video_ids),
            CountryRelevance.country == country,
            CountryRelevance.analyzed_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).all()
        
        results = {}
        for analysis in existing_analysis:
            results[analysis.video_id] = {
                'relevance_score': analysis.relevance_score,
                'reasoning': analysis.reasoning,
                'confidence_score': analysis.confidence_score,
                'origin_country': getattr(analysis, 'origin_country', 'UNKNOWN'),
                'analyzed_at': analysis.analyzed_at.isoformat(),
                'llm_model': analysis.llm_model
            }
        
        # Get missing videos for LLM analysis
        missing_video_ids = set(video_ids) - set(results.keys())
        
        if missing_video_ids:
            missing_videos = [v for v in videos if v['video_id'] in missing_video_ids]
            
            # Get LLM analysis for missing videos
            llm_results = llm_service.analyze_country_relevance_batch(missing_videos, country, query)
            results.update(llm_results)
            
            # Store LLM results in database
            for video_id, analysis in llm_results.items():
                try:
                    db_analysis = CountryRelevance(
                        video_id=video_id,
                        country=country,
                        relevance_score=analysis['relevance_score'],
                        reasoning=analysis['reasoning'],
                        confidence_score=analysis['confidence_score'],
                        origin_country=analysis.get('origin_country', 'UNKNOWN'),
                        llm_model=analysis['llm_model']
                    )
                    db.add(db_analysis)
                except Exception as e:
                    logger.error(f"Error storing country relevance for {video_id}: {e}")
            
            try:
                db.commit()
            except Exception as e:
                logger.error(f"Error committing country relevance data: {e}")
                db.rollback()
        
        return results
    
    def _get_google_trends_analysis(self, query: str, country: str, timeframe: str) -> Dict:
        """Get Google Trends analysis for cross-platform validation."""
        try:
            # Get Google Trends score
            trends_data = google_trends_service.get_trend_score(query, country, timeframe)
            
            # Get cross-platform validation
            validation_data = google_trends_service.validate_query_trending(
                query, country, youtube_trending=False  # Will be determined later
            )
            
            return {
                'trend_score': trends_data.get('trend_score', 0.0),
                'is_trending': trends_data.get('is_trending', False),
                'peak_interest': trends_data.get('peak_interest', 0),
                'validation_score': validation_data.get('validation_score', 0.0),
                'cross_platform_boost': validation_data.get('cross_platform_boost', 0.0),
                'platform_alignment': validation_data.get('platform_alignment', 'none'),
                'cache_hit': trends_data.get('cache_hit', False),
                'error': trends_data.get('error', None)
            }
        except Exception as e:
            logger.error(f"Error getting Google Trends analysis for '{query}': {e}")
            return {
                'trend_score': 0.0,
                'is_trending': False,
                'peak_interest': 0,
                'validation_score': 0.0,
                'cross_platform_boost': 0.0,
                'platform_alignment': 'none',
                'cache_hit': False,
                'error': str(e)
            }
    
    def calculate_v7_trending_score(self, video: Dict, country_relevance: float, 
                                   timeframe: str, is_in_trending_feed: bool = False, 
                                   google_trends_data: Dict = None) -> Dict:
        """Calculate MOMENTUM MVP trending score for a video."""
        try:
            # Get timeframe in hours
            timeframe_hours = get_timeframe_hours(timeframe)
            
            # Calculate video age in hours
            upload_date = video.get('upload_date')
            if isinstance(upload_date, str):
                upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
            
            age_hours = 0.0
            if upload_date:
                age_delta = datetime.now(timezone.utc) - upload_date.replace(tzinfo=timezone.utc)
                age_hours = age_delta.total_seconds() / 3600
            
            # Base MOMENTUM calculation
            views = max(video.get('views', 0), 1)
            likes = video.get('likes', 0)
            comments = video.get('comments', 0)
            
            # Calculate views per hour (within timeframe)
            effective_hours = min(age_hours, timeframe_hours)
            views_per_hour = views / max(effective_hours, 1)
            
            # Calculate engagement rate
            engagement_rate = (likes + comments) / views
            
            # Time decay factor (exponential decay)
            time_decay = math.exp(-age_hours / 24.0)  # Decay over 24 hours
            
            # Base momentum score
            base_momentum = (
                views_per_hour * 0.6 +
                engagement_rate * views * 0.3 +
                views * time_decay * 0.1
            )
            
            # MVP enhancements
            country_multiplier = 0.5 + (country_relevance * 1.5)  # 0.5-2.0x multiplier
            trending_feed_boost = 1.5 if is_in_trending_feed else 1.0
            
            # Google Trends enhancement
            google_trends_boost = 1.0
            google_trends_score = 0.0
            if google_trends_data:
                google_trends_score = google_trends_data.get('trend_score', 0.0)
                cross_platform_boost = google_trends_data.get('cross_platform_boost', 0.0)
                # Apply Google Trends boost: 1.0 to 1.3x based on trends data
                google_trends_boost = 1.0 + cross_platform_boost
            
            # Final trending score with Google Trends
            final_score = base_momentum * country_multiplier * trending_feed_boost * google_trends_boost
            
            return {
                'trending_score': final_score,
                'base_momentum': base_momentum,
                'country_relevance': country_relevance,
                'country_multiplier': country_multiplier,
                'trending_boost_applied': is_in_trending_feed,
                'google_trends_score': google_trends_score,
                'google_trends_boost': google_trends_boost,
                'normalized_score': min((final_score / 10000) * 10, 10),  # 0-10 scale
                'views_per_hour': views_per_hour,
                'engagement_rate': engagement_rate,
                'time_decay': time_decay,
                'age_hours': age_hours
            }
            
        except Exception as e:
            logger.error(f"Error calculating trending score for video {video.get('video_id')}: {e}")
            return {
                'trending_score': 0.0,
                'base_momentum': 0.0,
                'country_relevance': country_relevance,
                'country_multiplier': 1.0,
                'trending_boost_applied': False,
                'normalized_score': 0.0,
                'views_per_hour': 0.0,
                'engagement_rate': 0.0,
                'time_decay': 0.0,
                'age_hours': 0.0
            }
    
    def _calculate_trending_scores(self, videos: List[Dict], llm_results: Dict[str, Dict],
                                  country: str, timeframe: str, db: Session, 
                                  google_trends_data: Dict = None) -> List[Dict]:
        """Calculate trending scores for all videos."""
        scored_videos = []
        
        for video in videos:
            video_id = video['video_id']
            
            # Get country relevance score
            relevance_data = llm_results.get(video_id, {})
            country_relevance = relevance_data.get('relevance_score', 0.0)
            
            # Check if video is in trending feed
            is_in_trending_feed = video.get('is_in_trending_feed', False)
            
            # Calculate trending score with Google Trends
            score_data = self.calculate_v7_trending_score(
                video, country_relevance, timeframe, is_in_trending_feed, google_trends_data
            )
            
            # Combine video data with score data
            scored_video = {**video, **score_data}
            scored_video['country_relevance_reasoning'] = relevance_data.get('reasoning', '')
            scored_video['confidence_score'] = relevance_data.get('confidence_score', 0.5)
            scored_video['origin_country'] = relevance_data.get('origin_country', 'UNKNOWN')
            
            scored_videos.append(scored_video)
        
        return scored_videos
    
    def _apply_adaptive_filtering(self, scored_videos: List[Dict], limit: int, 
                                 query: str, country: str, timeframe: str, db: Session) -> List[Dict]:
        """Apply adaptive relevance thresholds to guarantee minimum results."""
        if not scored_videos:
            return []
        
        # Define threshold levels - adjusted for real-world relevance scores (avg ~0.1)
        threshold_levels = [0.4, 0.25, 0.15, 0.1, 0.05, 0.0]
        
        for threshold in threshold_levels:
            # Filter videos by current threshold
            filtered = [
                video for video in scored_videos 
                if video.get('country_relevance', 0.0) >= threshold
            ]
            
            logger.info(f"Threshold {threshold}: {len(filtered)} videos (target: {limit})")
            
            # If we have enough results, use this threshold
            if len(filtered) >= limit:
                return filtered[:limit * 2]  # Return slightly more for ranking flexibility
            
            # If we have some results but not enough, continue to next threshold
            # but keep these as backup
            if len(filtered) > 0:
                backup_results = filtered
        
        # If still not enough results with any threshold, implement fallback strategy
        if len(scored_videos) < limit:
            logger.warning(f"Only {len(scored_videos)} videos found for '{query}' in {country}. "
                          f"Attempting fallback search...")
            
            # Attempt broader search as fallback
            fallback_videos = self._fallback_search(query, country, timeframe, db, limit - len(scored_videos))
            
            if fallback_videos:
                # Get LLM analysis for fallback videos
                fallback_llm = self._get_country_relevance_analysis(fallback_videos, country, db, query)
                
                # Calculate scores for fallback videos (without Google Trends for fallback)
                fallback_scored = self._calculate_trending_scores(fallback_videos, fallback_llm, country, timeframe, db, None)
                
                # Combine with existing results
                scored_videos.extend(fallback_scored)
                
                logger.info(f"Added {len(fallback_scored)} fallback videos. Total: {len(scored_videos)}")
        
        # Return all available videos if we still don't have enough
        return scored_videos[:limit * 2] if len(scored_videos) > limit else scored_videos
    
    def _fallback_search(self, query: str, country: str, timeframe: str, db: Session, needed_count: int) -> List[Dict]:
        """Perform broader fallback search when not enough results."""
        try:
            processor = CountryProcessorFactory.get_processor(country)
            timeframe_hours = get_timeframe_hours(timeframe)
            published_after = datetime.now(timezone.utc) - timedelta(hours=timeframe_hours)
            
            # Strategy 1: Generic trending terms for the country
            generic_terms = processor.get_generic_trending_terms()
            fallback_videos = []
            
            for term in generic_terms:
                if len(fallback_videos) >= needed_count:
                    break
                    
                videos = youtube_service.search_videos(
                    term, 
                    country, 
                    max_results=needed_count,
                    published_after=published_after
                )
                
                for video in videos:
                    if video['video_id'] not in [v.get('video_id') for v in fallback_videos]:
                        fallback_videos.append(video)
                        
                        if len(fallback_videos) >= needed_count:
                            break
            
            # Strategy 2: If still not enough, get broader trending feed
            if len(fallback_videos) < needed_count:
                trending_videos = youtube_service.get_trending_videos(country, max_results=needed_count * 2)
                
                for video in trending_videos:
                    if len(fallback_videos) >= needed_count:
                        break
                        
                    if video['video_id'] not in [v.get('video_id') for v in fallback_videos]:
                        # Check if video is within timeframe
                        upload_date = video.get('upload_date')
                        if upload_date:
                            if isinstance(upload_date, str):
                                upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
                            
                            if upload_date >= published_after:
                                fallback_videos.append(video)
            
            # Get detailed info for fallback videos
            if fallback_videos:
                video_ids = [v['video_id'] for v in fallback_videos]
                detailed_videos = youtube_service.get_video_details(video_ids)
                
                final_fallback = []
                for video_id, video_data in detailed_videos.items():
                    video_data['is_in_trending_feed'] = True  # Mark as trending feed source
                    final_fallback.append(video_data)
                
                logger.info(f"Fallback search found {len(final_fallback)} additional videos")
                return final_fallback
            
            return []
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []
    
    def _rank_and_format_results(self, scored_videos: List[Dict], limit: int) -> List[Dict]:
        """Rank videos by trending score and format for API response."""
        # Sort by trending score (descending)
        sorted_videos = sorted(scored_videos, key=lambda x: x['trending_score'], reverse=True)
        
        # Format top results
        formatted_results = []
        for rank, video in enumerate(sorted_videos[:limit], 1):
            result = {
                'rank': rank,
                'video_id': video['video_id'],
                'title': video['title'],
                'channel': video['channel_name'],
                'channel_country': video.get('channel_country', ''),
                'origin_country': video.get('origin_country', 'UNKNOWN'),
                'views': video['views'],
                'views_in_timeframe': int(video['views_per_hour'] * get_timeframe_hours(video.get('timeframe', '48h'))),
                'likes': video['likes'],
                'comments': video['comments'],
                'trending_score': round(video['trending_score'], 2),
                'country_relevance_score': round(video['country_relevance'], 3),
                'is_in_trending_feed': video.get('is_in_trending_feed', False),
                'reasoning': video.get('country_relevance_reasoning', ''),
                'url': f"https://youtube.com/watch?v={video['video_id']}",
                'thumbnail': video.get('thumbnail_url', ''),
                'upload_date': video['upload_date'].isoformat() if video.get('upload_date') else None,
                'age_hours': round(video.get('age_hours', 0), 1),
                'engagement_rate': round(video['engagement_rate'] * 100, 2)  # As percentage
            }
            formatted_results.append(result)
        
        return formatted_results
    
    def _count_trending_matches(self, results: List[Dict]) -> int:
        """Count how many results are in official trending feed."""
        return sum(1 for r in results if r.get('is_in_trending_feed', False))
    
    def _empty_result(self, query: str, country: str, timeframe: str, message: str) -> Dict:
        """Create empty result structure."""
        return {
            "success": True,
            "query": query,
            "country": country,
            "timeframe": timeframe,
            "algorithm": self.algorithm_version,
            "processing_time_ms": 0,
            "results": [],
            "metadata": {
                "total_analyzed": 0,
                "llm_analyzed": 0,
                "cache_hit": False,
                "trending_feed_matches": 0,
                "llm_cost_cents": 0,
                "message": message
            }
        }
    
    def _error_result(self, query: str, country: str, timeframe: str, error: str) -> Dict:
        """Create error result structure."""
        return {
            "success": False,
            "query": query,
            "country": country,
            "timeframe": timeframe,
            "algorithm": self.algorithm_version,
            "processing_time_ms": 0,
            "results": [],
            "error": error,
            "metadata": {
                "total_analyzed": 0,
                "llm_analyzed": 0,
                "cache_hit": False,
                "trending_feed_matches": 0,
                "llm_cost_cents": 0
            }
        }


# Create global trending service instance
trending_service = TrendingService()