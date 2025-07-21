from abc import ABC, abstractmethod
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class CountryProcessor(ABC):
    """Abstract base class for country-specific processors."""
    
    def __init__(self, country_code: str):
        self.country_code = country_code
        self.country_name = self._get_country_name()
    
    @abstractmethod
    def get_local_search_terms(self, query: str) -> List[str]:
        """Generate country-specific search variants."""
        pass
    
    @abstractmethod
    def get_relevance_criteria(self) -> str:
        """Get LLM prompt criteria for this country."""
        pass
    
    @abstractmethod
    def get_cultural_context(self) -> Dict:
        """Get cultural patterns and context for analysis."""
        pass
    
    def _get_country_name(self) -> str:
        """Get country name from country code."""
        country_names = {
            'DE': 'Germany',
            'US': 'USA',
            'FR': 'France',
            'JP': 'Japan'
        }
        return country_names.get(self.country_code, self.country_code)
    
    def get_timezone(self) -> str:
        """Get primary timezone for the country."""
        timezones = {
            'DE': 'Europe/Berlin',
            'US': 'America/New_York',
            'FR': 'Europe/Paris',
            'JP': 'Asia/Tokyo'
        }
        return timezones.get(self.country_code, 'UTC')
    
    def get_prime_time_hours(self) -> tuple:
        """Get prime time hours (start, end) in 24h format."""
        prime_times = {
            'DE': (19, 22),  # 7 PM - 10 PM
            'US': (20, 23),  # 8 PM - 11 PM
            'FR': (20, 22),  # 8 PM - 10 PM
            'JP': (19, 22),  # 7 PM - 10 PM
        }
        return prime_times.get(self.country_code, (20, 22))


class GermanyProcessor(CountryProcessor):
    """Processor for German market."""
    
    def __init__(self):
        super().__init__('DE')
    
    def get_local_search_terms(self, query: str) -> List[str]:
        """Generate German search variants."""
        base_terms = [
            f"{query}",
            f"{query} deutsch",
            f"deutsche {query}",
            f"{query} germany",
            f"{query} deutschland"
        ]
        
        # Add common German prefixes/suffixes
        german_variants = []
        if query.lower() not in ['der', 'die', 'das', 'und', 'oder']:
            german_variants.extend([
                f"deutsches {query}",
                f"{query} auf deutsch",
                f"{query} german"
            ])
        
        return list(set(base_terms + german_variants))[:8]
    
    def get_relevance_criteria(self) -> str:
        """Get German relevance criteria."""
        return """
        Criteria for Germany relevance:
        - German language content (Deutsch) or German subtitles
        - German YouTubers or Germany-focused content
        - Discussion in German communities (German comments)
        - Topics relevant for German audience (culture, news, entertainment)
        - Views/engagement during German prime time (19-22 Uhr MEZ/MESZ)
        - German cultural references, humor, and context
        - Content about German cities, events, or personalities
        - Use of German internet slang and expressions
        """
    
    def get_cultural_context(self) -> Dict:
        """Get German cultural context."""
        return {
            'language_indicators': [
                'deutsch', 'german', 'germany', 'deutschland', 'berlin', 'münchen', 
                'hamburg', 'köln', 'frankfurt', 'bavaria', 'bayern'
            ],
            'cultural_keywords': [
                'bundesliga', 'oktoberfest', 'bratwurst', 'bier', 'merkel',
                'autobahn', 'lederhosen', 'currywurst', 'döner'
            ],
            'common_expressions': [
                'hallo', 'guten tag', 'danke', 'bitte', 'tschüss', 
                'wie geht\'s', 'alles klar', 'genau', 'ach so'
            ],
            'popular_topics': [
                'fußball', 'bundesliga', 'politik', 'nachrichten', 'musik',
                'gaming', 'comedy', 'food', 'travel', 'tech'
            ],
            'time_zone': 'Europe/Berlin',
            'prime_time': '19:00-22:00',
            'weekend_activity_peak': 'Saturday 14:00-18:00'
        }


class USAProcessor(CountryProcessor):
    """Processor for US market."""
    
    def __init__(self):
        super().__init__('US')
    
    def get_local_search_terms(self, query: str) -> List[str]:
        """Generate US search variants."""
        base_terms = [
            f"{query}",
            f"{query} america",
            f"american {query}",
            f"{query} usa",
            f"{query} us"
        ]
        
        # Add common American variants
        american_variants = []
        if len(query.split()) == 1:  # Single word queries
            american_variants.extend([
                f"{query} united states",
                f"{query} american style",
                f"us {query}"
            ])
        
        return list(set(base_terms + american_variants))[:8]
    
    def get_relevance_criteria(self) -> str:
        """Get US relevance criteria."""
        return """
        Criteria for USA relevance:
        - English language content (American English)
        - American creators or US-focused content
        - Discussion patterns typical for US audience
        - Topics relevant for American viewers (culture, politics, sports)
        - Views/engagement during US prime times (EST/PST)
        - American cultural references and humor
        - Content about US cities, states, or American personalities
        - Use of American slang and expressions
        """
    
    def get_cultural_context(self) -> Dict:
        """Get American cultural context."""
        return {
            'language_indicators': [
                'america', 'american', 'usa', 'united states', 'us',
                'new york', 'california', 'texas', 'florida'
            ],
            'cultural_keywords': [
                'nfl', 'nba', 'mlb', 'super bowl', 'thanksgiving', 
                'fourth of july', 'halloween', 'black friday'
            ],
            'common_expressions': [
                'hey', 'what\'s up', 'awesome', 'dude', 'bro',
                'totally', 'for sure', 'no way', 'oh my god'
            ],
            'popular_topics': [
                'football', 'basketball', 'politics', 'news', 'music',
                'gaming', 'comedy', 'food', 'travel', 'tech'
            ],
            'time_zone': 'America/New_York',
            'prime_time': '20:00-23:00',
            'weekend_activity_peak': 'Sunday 13:00-17:00'
        }


class FranceProcessor(CountryProcessor):
    """Processor for French market."""
    
    def __init__(self):
        super().__init__('FR')
    
    def get_local_search_terms(self, query: str) -> List[str]:
        """Generate French search variants."""
        base_terms = [
            f"{query}",
            f"{query} français",
            f"{query} france",
            f"français {query}",
            f"{query} francais"
        ]
        
        # Add common French variants
        french_variants = []
        if query.lower() not in ['le', 'la', 'les', 'et', 'ou']:
            french_variants.extend([
                f"{query} en français",
                f"french {query}",
                f"{query} french"
            ])
        
        return list(set(base_terms + french_variants))[:8]
    
    def get_relevance_criteria(self) -> str:
        """Get French relevance criteria."""
        return """
        Criteria for France relevance:
        - French language content (Français) or French subtitles
        - French creators or France-focused content
        - French cultural references and discussions
        - Topics relevant for French audience (culture, politics, entertainment)
        - Views/engagement during French prime times (20-22h CET)
        - French humor, cultural nuances, and references
        - Content about French cities, regions, or French personalities
        - Use of French internet slang and expressions
        """
    
    def get_cultural_context(self) -> Dict:
        """Get French cultural context."""
        return {
            'language_indicators': [
                'france', 'french', 'français', 'paris', 'lyon',
                'marseille', 'toulouse', 'nice', 'bordeaux'
            ],
            'cultural_keywords': [
                'baguette', 'croissant', 'champagne', 'macron', 
                'tour de france', 'cannes', 'louvre', 'versailles'
            ],
            'common_expressions': [
                'bonjour', 'salut', 'merci', 'au revoir', 'oui',
                'non', 'comment allez-vous', 'ça va', 'très bien'
            ],
            'popular_topics': [
                'football', 'ligue 1', 'politique', 'actualités', 'musique',
                'gaming', 'comédie', 'cuisine', 'voyage', 'tech'
            ],
            'time_zone': 'Europe/Paris',
            'prime_time': '20:00-22:00',
            'weekend_activity_peak': 'Sunday 15:00-19:00'
        }


class JapanProcessor(CountryProcessor):
    """Processor for Japanese market."""
    
    def __init__(self):
        super().__init__('JP')
    
    def get_local_search_terms(self, query: str) -> List[str]:
        """Generate Japanese search variants."""
        base_terms = [
            f"{query}",
            f"{query} 日本",
            f"{query} japan",
            f"japanese {query}",
            f"{query} にほん"
        ]
        
        # Add common Japanese variants
        japanese_variants = []
        if len(query.split()) == 1:
            japanese_variants.extend([
                f"{query} 日本語",
                f"日本の{query}",
                f"{query} jpn"
            ])
        
        return list(set(base_terms + japanese_variants))[:8]
    
    def get_relevance_criteria(self) -> str:
        """Get Japanese relevance criteria."""
        return """
        Criteria for Japan relevance:
        - Japanese language content (hiragana, katakana, kanji) or Japanese subtitles
        - Japanese creators or Japan-focused content
        - Japanese cultural context and references
        - Topics relevant for Japanese audience (culture, anime, J-pop, etc.)
        - Views/engagement during Japanese prime times (19-22h JST)
        - Japanese humor, cultural nuances, and references
        - Content about Japanese cities, culture, or Japanese personalities
        - Use of Japanese internet culture and expressions
        """
    
    def get_cultural_context(self) -> Dict:
        """Get Japanese cultural context."""
        return {
            'language_indicators': [
                'japan', 'japanese', 'nihon', 'nippon', 'tokyo',
                'osaka', 'kyoto', 'yokohama', 'nagoya', '日本'
            ],
            'cultural_keywords': [
                'anime', 'manga', 'jpop', 'sushi', 'ramen',
                'pokemon', 'nintendo', 'sony', 'toyota', 'sakura'
            ],
            'common_expressions': [
                'こんにちは', 'arigatou', 'konnichiwa', 'sayonara', 'arigato',
                'ohayo', 'konbanwa', 'sumimasen', 'gomen'
            ],
            'popular_topics': [
                'anime', 'manga', 'jpop', 'gaming', 'tech',
                'food', 'travel', 'culture', 'baseball', 'sumo'
            ],
            'time_zone': 'Asia/Tokyo',
            'prime_time': '19:00-22:00',
            'weekend_activity_peak': 'Sunday 14:00-18:00'
        }


class CountryProcessorFactory:
    """Factory for creating country processors."""
    
    _processors = {
        'DE': GermanyProcessor,
        'US': USAProcessor, 
        'FR': FranceProcessor,
        'JP': JapanProcessor
    }
    
    @classmethod
    def get_processor(cls, country_code: str) -> CountryProcessor:
        """Get processor for country code."""
        processor_class = cls._processors.get(country_code)
        
        if not processor_class:
            logger.error(f"No processor available for country code: {country_code}")
            raise ValueError(f"Unsupported country code: {country_code}")
        
        return processor_class()
    
    @classmethod
    def get_supported_countries(cls) -> List[str]:
        """Get list of supported country codes."""
        return list(cls._processors.keys())
    
    @classmethod
    def get_all_processors(cls) -> Dict[str, CountryProcessor]:
        """Get all available processors."""
        return {code: cls.get_processor(code) for code in cls._processors.keys()}