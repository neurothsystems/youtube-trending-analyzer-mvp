import logging
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import asyncio
import re
from app.core.config import settings
from app.core.redis import CacheManager, get_llm_cache_key

logger = logging.getLogger(__name__)


class LLMService:
    """Google Gemini Flash LLM integration for country relevance analysis."""
    
    def __init__(self):
        """Initialize Gemini API client."""
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not configured")
            self.model = None
            return
        
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Configure safety settings for less restrictive content filtering
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # Initialize Gemini Flash model
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                safety_settings=safety_settings
            )
            
            logger.info("Gemini Flash LLM client initialized successfully")
            
            # Initialize cost tracking
            self.daily_cost = 0.0
            self.monthly_cost = 0.0
            self.token_count = 0
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API client: {e}")
            self.model = None
    
    def _is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.model is not None
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimation: ~4 characters per token for mixed content
        return len(text) // 4
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for Gemini Flash API call."""
        # Gemini Flash pricing: $0.20 per 1M tokens (as of spec)
        cost_per_token = 0.20 / 1_000_000
        total_tokens = input_tokens + output_tokens
        return total_tokens * cost_per_token
    
    def _track_cost(self, cost: float):
        """Track API costs for budget monitoring."""
        self.daily_cost += cost
        self.monthly_cost += cost
        
        if self.monthly_cost > settings.LLM_MONTHLY_BUDGET:
            logger.warning(f"Monthly LLM budget exceeded: €{self.monthly_cost:.2f} / €{settings.LLM_MONTHLY_BUDGET}")
    
    def analyze_country_relevance_batch(self, videos: List[Dict], target_country: str) -> Dict[str, Dict]:
        """Analyze country relevance for a batch of videos (budget optimized)."""
        if not self._is_available():
            logger.error("LLM service not available")
            return {}
        
        if not videos:
            return {}
        
        # Check cache first
        video_ids = [v['video_id'] for v in videos]
        cache_key = get_llm_cache_key(video_ids, target_country)
        cached_result = CacheManager.cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Retrieved LLM analysis from cache for {len(videos)} videos in {target_country}")
            return cached_result
        
        try:
            # Prepare batch prompt
            prompt = self._build_country_relevance_prompt(videos, target_country)
            
            # Estimate input tokens
            input_tokens = self._estimate_tokens(prompt)
            
            # Check budget before making call
            estimated_cost = self._calculate_cost(input_tokens, input_tokens // 2)  # Estimate output as half of input
            
            if self.monthly_cost + estimated_cost > settings.LLM_MONTHLY_BUDGET:
                logger.error(f"LLM budget limit would be exceeded. Current: €{self.monthly_cost:.2f}, Estimated cost: €{estimated_cost:.2f}")
                return {}
            
            # Make API call
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,  # Low temperature for consistent results
                    'max_output_tokens': 8192,
                }
            )
            
            # Process response
            if response.text:
                # Estimate output tokens and calculate actual cost
                output_tokens = self._estimate_tokens(response.text)
                actual_cost = self._calculate_cost(input_tokens, output_tokens)
                self._track_cost(actual_cost)
                
                # Parse the response
                results = self._parse_country_relevance_response(response.text, video_ids)
                
                # Cache the results for 6 hours (budget optimization)
                CacheManager.cache.set(cache_key, results, 21600)
                
                logger.info(f"Analyzed {len(results)} videos for {target_country}. Cost: €{actual_cost:.4f}")
                return results
            else:
                logger.error("Empty response from LLM")
                return {}
                
        except Exception as e:
            logger.error(f"LLM country relevance analysis error: {e}")
            return {}
    
    def _build_country_relevance_prompt(self, videos: List[Dict], target_country: str) -> str:
        """Build prompt for country relevance analysis."""
        country_criteria = {
            'DE': """
            Criteria for Germany relevance:
            - German language content or German subtitles
            - German YouTubers or Germany-focused content
            - Discussion in German communities (comments)
            - Topics relevant for German audience
            - Views/engagement during German prime time
            - German cultural references and context
            """,
            'US': """
            Criteria for USA relevance:
            - English language content
            - American creators or US-focused content
            - Discussion patterns typical for US audience
            - Topics relevant for American viewers
            - Views/engagement during US prime times
            - American cultural references and context
            """,
            'FR': """
            Criteria for France relevance:
            - French language content
            - French creators or France-focused content
            - French cultural references and discussions
            - Topics relevant for French audience
            - Views/engagement during French prime times
            - French cultural context and references
            """,
            'JP': """
            Criteria for Japan relevance:
            - Japanese language content (hiragana, katakana, kanji)
            - Japanese creators or Japan-focused content
            - Japanese cultural context and references
            - Topics relevant for Japanese audience
            - Views/engagement during Japanese prime times (JST)
            - Japanese cultural nuances and references
            """
        }
        
        criteria = country_criteria.get(target_country, country_criteria['US'])
        
        # Format video list
        video_list = []
        for video in videos[:settings.LLM_BATCH_SIZE]:  # Limit batch size
            video_info = f"""
Video ID: {video['video_id']}
Title: {video.get('title', 'N/A')}
Channel: {video.get('channel_name', 'N/A')}
Description: {(video.get('description', '')[:200] + '...') if len(video.get('description', '')) > 200 else video.get('description', '')}
Views: {video.get('views', 0)}
Upload Date: {video.get('upload_date', 'N/A')}
"""
            video_list.append(video_info)
        
        videos_text = '\n---\n'.join(video_list)
        
        prompt = f"""
Analyze these YouTube videos for {target_country} trending relevance. Rate each video's relevance to {target_country} on a scale from 0.0 to 1.0.

{criteria}

Videos to analyze:
{videos_text}

For each video, provide your analysis in this EXACT format:
VIDEO_ID: <video_id>
SCORE: <score between 0.0 and 1.0>
REASONING: <brief explanation why this score was given>
CONFIDENCE: <confidence in analysis between 0.0 and 1.0>
ORIGIN: <estimated video origin country: DE/US/FR/JP/UNKNOWN>

Rules:
- Be precise with scores (use decimals like 0.85, 0.23, etc.)
- Keep reasoning under 100 words
- Consider language, cultural context, creator origin, and audience engagement patterns
- A score of 0.0 means completely irrelevant to {target_country}
- A score of 1.0 means highly relevant and likely to trend specifically in {target_country}
- ORIGIN should be the likely origin country of the video/channel (DE/US/FR/JP/UNKNOWN)
- Provide analysis for ALL videos, even if some data is missing

Begin analysis:
"""
        return prompt
    
    def _parse_country_relevance_response(self, response_text: str, video_ids: List[str]) -> Dict[str, Dict]:
        """Parse LLM response for country relevance scores."""
        results = {}
        
        try:
            # Split response into video blocks
            video_blocks = re.split(r'VIDEO_ID:', response_text)[1:]  # Skip first empty part
            
            for block in video_blocks:
                try:
                    lines = block.strip().split('\n')
                    if not lines:
                        continue
                    
                    # Extract video ID from first line
                    video_id = lines[0].strip()
                    
                    # Initialize default values
                    score = 0.0
                    reasoning = "No reasoning provided"
                    confidence = 0.5
                    
                    # Parse remaining lines
                    origin_country = 'UNKNOWN'
                    for line in lines[1:]:
                        line = line.strip()
                        if line.startswith('SCORE:'):
                            try:
                                score = float(line.replace('SCORE:', '').strip())
                                score = max(0.0, min(1.0, score))  # Clamp to valid range
                            except:
                                score = 0.0
                        
                        elif line.startswith('REASONING:'):
                            reasoning = line.replace('REASONING:', '').strip()
                        
                        elif line.startswith('CONFIDENCE:'):
                            try:
                                confidence = float(line.replace('CONFIDENCE:', '').strip())
                                confidence = max(0.0, min(1.0, confidence))  # Clamp to valid range
                            except:
                                confidence = 0.5
                        
                        elif line.startswith('ORIGIN:'):
                            origin = line.replace('ORIGIN:', '').strip().upper()
                            if origin in ['DE', 'US', 'FR', 'JP']:
                                origin_country = origin
                    
                    # Store result if video ID is valid
                    if video_id and video_id in video_ids:
                        results[video_id] = {
                            'relevance_score': score,
                            'reasoning': reasoning,
                            'confidence_score': confidence,
                            'origin_country': origin_country,
                            'analyzed_at': datetime.now(timezone.utc).isoformat(),
                            'llm_model': 'gemini-flash'
                        }
                
                except Exception as e:
                    logger.error(f"Error parsing video block: {e}")
                    continue
            
            # Fill in missing videos with default scores
            for video_id in video_ids:
                if video_id not in results:
                    results[video_id] = {
                        'relevance_score': 0.0,
                        'reasoning': 'Analysis failed or not provided',
                        'confidence_score': 0.1,
                        'origin_country': 'UNKNOWN',
                        'analyzed_at': datetime.now(timezone.utc).isoformat(),
                        'llm_model': 'gemini-flash'
                    }
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            
            # Return default results for all videos
            for video_id in video_ids:
                results[video_id] = {
                    'relevance_score': 0.0,
                    'reasoning': 'Failed to parse LLM response',
                    'confidence_score': 0.1,
                    'origin_country': 'UNKNOWN',
                    'analyzed_at': datetime.now(timezone.utc).isoformat(),
                    'llm_model': 'gemini-flash'
                }
        
        return results
    
    def expand_search_terms(self, query: str, target_country: str) -> List[str]:
        """Generate country-specific search term variants using LLM."""
        if not self._is_available():
            logger.error("LLM service not available") 
            return [query]  # Return original query as fallback
        
        try:
            prompt = f"""
Generate 5 search term variations for finding trending YouTube content in {target_country} related to "{query}".

Consider:
- Local language variants and translations
- Cultural context and popular formats
- Regional slang and terminology
- Popular content creator naming conventions
- Common hashtag patterns

Target country: {target_country}
Original query: "{query}"

Provide ONLY the search terms, one per line, without numbering or explanations:
"""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 1024,
                }
            )
            
            if response.text:
                # Parse search terms
                terms = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
                
                # Include original query and limit to 5 terms total
                all_terms = [query] + terms
                return list(set(all_terms))[:5]  # Remove duplicates and limit
            
        except Exception as e:
            logger.error(f"Error expanding search terms: {e}")
        
        return [query]  # Fallback to original query
    
    def get_cost_info(self) -> Dict:
        """Get current cost information and budget status."""
        budget_used_percentage = (self.monthly_cost / settings.LLM_MONTHLY_BUDGET) * 100
        
        return {
            'daily_cost_eur': round(self.daily_cost, 4),
            'monthly_cost_eur': round(self.monthly_cost, 4),
            'monthly_budget_eur': settings.LLM_MONTHLY_BUDGET,
            'budget_remaining_eur': round(settings.LLM_MONTHLY_BUDGET - self.monthly_cost, 4),
            'budget_used_percentage': round(budget_used_percentage, 2),
            'estimated_tokens_processed': self.token_count,
            'cost_per_million_tokens': 0.20,
            'batch_size': settings.LLM_BATCH_SIZE
        }


# Create global LLM service instance
llm_service = LLMService()