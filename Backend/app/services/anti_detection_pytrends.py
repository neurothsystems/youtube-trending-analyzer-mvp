"""
Anti-Detection Google Trends Module - Production-Hardened for Render.com

Advanced anti-detection strategies, monitoring, and production optimizations
specifically designed for cloud platforms with shared IP addresses.

Created by DevOps Expert for maximum production reliability.
"""

import logging
import random
import time
import json
import platform
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from collections import defaultdict, deque
import threading
import os
import ssl
import socket
from urllib.parse import urlencode
import secrets

# Third-party imports
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import user_agents

# Local imports
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserAgentRotator:
    """Advanced user agent rotation with realistic browser fingerprints."""
    
    def __init__(self):
        self.user_agents = self._generate_realistic_user_agents()
        self.current_index = 0
        self._lock = threading.Lock()
    
    def _generate_realistic_user_agents(self) -> List[str]:
        """Generate realistic user agents based on current market share."""
        
        # Chrome versions (dominant market share)
        chrome_versions = ['120.0.0.0', '119.0.0.0', '121.0.0.0', '118.0.0.0']
        
        # Firefox versions
        firefox_versions = ['121.0', '120.0', '119.0', '122.0']
        
        # Safari versions
        safari_versions = ['17.1', '17.0', '16.6', '17.2']
        
        # Edge versions
        edge_versions = ['120.0.0.0', '119.0.0.0', '121.0.0.0']
        
        user_agents = []
        
        # Chrome Windows (40% of traffic)
        for version in chrome_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
                f'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
            ])
        
        # Chrome macOS (15% of traffic)
        for version in chrome_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
                f'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
            ])
        
        # Firefox Windows (8% of traffic)
        for version in firefox_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}',
                f'Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:{version}) Gecko/20100101 Firefox/{version}',
            ])
        
        # Safari macOS (10% of traffic)
        for version in safari_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15',
                f'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{version} Safari/605.1.15',
            ])
        
        # Edge Windows (5% of traffic)
        for version in edge_versions:
            user_agents.extend([
                f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36 Edg/{version}',
            ])
        
        # Chrome Linux (server detection mitigation - 2% of traffic)
        for version in chrome_versions[:2]:
            user_agents.extend([
                f'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36',
            ])
        
        return user_agents
    
    def get_random_user_agent(self) -> str:
        """Get random user agent."""
        return random.choice(self.user_agents)
    
    def get_next_user_agent(self) -> str:
        """Get next user agent in rotation."""
        with self._lock:
            ua = self.user_agents[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.user_agents)
            return ua


class HeaderGenerator:
    """Generate realistic browser headers to avoid detection."""
    
    def __init__(self):
        self.languages = [
            'en-US,en;q=0.9',
            'de-DE,de;q=0.9,en;q=0.8',
            'fr-FR,fr;q=0.9,en;q=0.8',
            'en-GB,en;q=0.9',
            'es-ES,es;q=0.9,en;q=0.8',
            'it-IT,it;q=0.9,en;q=0.8'
        ]
        
        self.encodings = [
            'gzip, deflate, br',
            'gzip, deflate, br, zstd',
            'gzip, deflate'
        ]
        
        # Realistic screen resolutions
        self.screen_resolutions = [
            '1920x1080', '1366x768', '1536x864', '1440x900',
            '1280x720', '2560x1440', '3840x2160', '1600x900'
        ]
        
        # Realistic viewport sizes (smaller than screen)
        self.viewport_sizes = [
            '1903x927', '1349x695', '1519x791', '1423x827',
            '1263x647', '2543x1367', '3823x2087', '1583x827'
        ]
    
    def generate_headers(self, user_agent: str) -> Dict[str, str]:
        """Generate realistic headers for user agent."""
        
        # Detect browser type from user agent
        is_chrome = 'Chrome' in user_agent and 'Edg' not in user_agent
        is_firefox = 'Firefox' in user_agent
        is_safari = 'Safari' in user_agent and 'Chrome' not in user_agent
        is_edge = 'Edg' in user_agent
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': random.choice(self.languages),
            'Accept-Encoding': random.choice(self.encodings),
            'DNT': random.choice(['1', '0']),  # Do Not Track
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Browser-specific headers
        if is_chrome or is_edge:
            headers.update({
                'sec-ch-ua': self._generate_sec_ch_ua(user_agent),
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': self._get_platform_hint(user_agent),
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })
        
        elif is_firefox:
            headers.update({
                'Cache-Control': 'max-age=0',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'TE': 'trailers',
            })
        
        elif is_safari:
            headers.update({
                'Cache-Control': 'max-age=0',
            })
        
        # Add realistic viewport dimensions
        viewport = random.choice(self.viewport_sizes)
        headers['sec-ch-viewport-width'] = viewport.split('x')[0]
        
        return headers
    
    def _generate_sec_ch_ua(self, user_agent: str) -> str:
        """Generate sec-ch-ua header based on user agent."""
        if 'Chrome/120' in user_agent:
            return '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        elif 'Chrome/119' in user_agent:
            return '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"'
        elif 'Chrome/121' in user_agent:
            return '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"'
        elif 'Edg' in user_agent:
            return '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"'
        else:
            return '"Chromium";v="120", "Not_A Brand";v="8"'
    
    def _get_platform_hint(self, user_agent: str) -> str:
        """Get platform hint from user agent."""
        if 'Windows NT 10.0' in user_agent or 'Windows NT 11.0' in user_agent:
            return '"Windows"'
        elif 'Macintosh' in user_agent:
            return '"macOS"'
        elif 'Linux' in user_agent:
            return '"Linux"'
        else:
            return '"Windows"'


class TimingManager:
    """Manage request timing to mimic human behavior."""
    
    def __init__(self):
        self.last_request_time = 0
        self.request_history = deque(maxlen=50)  # Track last 50 requests
        self._lock = threading.Lock()
    
    def calculate_delay(self, is_retry: bool = False, failure_count: int = 0) -> float:
        """Calculate optimal delay before next request."""
        base_delay = 5.0  # Increased from 3.0 for better stealth
        
        # Human-like variation (3-8 seconds base)
        human_delay = random.uniform(3.0, 8.0)
        
        # Retry backoff
        if is_retry:
            retry_multiplier = min(2.0 ** failure_count, 8.0)  # Max 8x multiplier
            human_delay *= retry_multiplier
        
        # Time-of-day adjustment (slower during peak hours)
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:  # Business hours
            human_delay *= 1.3
        elif 18 <= current_hour <= 22:  # Evening peak
            human_delay *= 1.5
        
        # Request frequency adjustment
        with self._lock:
            recent_requests = len([t for t in self.request_history if time.time() - t < 300])  # Last 5 minutes
            if recent_requests > 10:  # More than 10 requests in 5 minutes
                human_delay *= 2.0
            elif recent_requests > 5:
                human_delay *= 1.5
        
        # Add jitter to avoid patterns
        jitter = random.uniform(-0.3, 0.3)
        final_delay = human_delay * (1 + jitter)
        
        return max(final_delay, 2.0)  # Minimum 2 seconds
    
    def wait_if_needed(self, is_retry: bool = False, failure_count: int = 0):
        """Wait appropriate amount of time before request."""
        with self._lock:
            current_time = time.time()
            
            if self.last_request_time > 0:
                delay = self.calculate_delay(is_retry, failure_count)
                elapsed = current_time - self.last_request_time
                
                if elapsed < delay:
                    wait_time = delay - elapsed
                    logger.debug(f"Waiting {wait_time:.2f}s before request (retry: {is_retry}, failures: {failure_count})")
                    time.sleep(wait_time)
            
            self.last_request_time = time.time()
            self.request_history.append(self.last_request_time)


class RenderOptimizer:
    """Render.com specific optimizations."""
    
    def __init__(self):
        self.render_detected = self._detect_render_environment()
        if self.render_detected:
            logger.info("Render.com environment detected - applying optimizations")
    
    def _detect_render_environment(self) -> bool:
        """Detect if running on Render.com."""
        render_indicators = [
            os.getenv('RENDER'),
            os.getenv('RENDER_SERVICE_ID'),
            'render.com' in os.getenv('RENDER_EXTERNAL_URL', ''),
            'onrender.com' in os.getenv('RENDER_EXTERNAL_HOSTNAME', '')
        ]
        
        return any(render_indicators)
    
    def get_optimized_session_config(self) -> Dict:
        """Get optimized session configuration for Render.com."""
        config = {
            'timeout': (20, 45),  # Longer timeouts for shared infrastructure
            'max_retries': 3,
            'backoff_factor': 0.5,
            'pool_connections': 2,  # Reduced for memory constraints
            'pool_maxsize': 5,
            'verify': True,
        }
        
        if self.render_detected:
            # Render-specific optimizations
            config.update({
                'timeout': (25, 60),  # Even longer timeouts
                'max_retries': 2,  # Fewer retries to avoid memory issues
                'pool_connections': 1,  # Minimal connection pool
                'pool_maxsize': 3,
            })
        
        return config
    
    def get_memory_optimized_cache_size(self) -> int:
        """Get optimal cache size for Render.com memory limits."""
        if self.render_detected:
            return 500  # Smaller cache for 1GB memory limit
        else:
            return 1000  # Default cache size


class ProductionMonitor:
    """Production monitoring and alerting system."""
    
    def __init__(self):
        self.metrics = defaultdict(int)
        self.success_rates = deque(maxlen=100)  # Track success rates
        self.response_times = deque(maxlen=100)  # Track response times
        self.error_patterns = defaultdict(int)
        self._lock = threading.Lock()
        
        # Alert thresholds
        self.success_rate_threshold = 0.5  # Alert if below 50%
        self.response_time_threshold = 30.0  # Alert if above 30s
        self.error_rate_threshold = 0.7  # Alert if error rate above 70%
    
    def record_request(self, success: bool, response_time: float, error_type: Optional[str] = None):
        """Record request metrics."""
        with self._lock:
            self.metrics['total_requests'] += 1
            
            if success:
                self.metrics['successful_requests'] += 1
                self.success_rates.append(1)
            else:
                self.metrics['failed_requests'] += 1
                self.success_rates.append(0)
                
                if error_type:
                    self.error_patterns[error_type] += 1
            
            self.response_times.append(response_time)
    
    def get_current_success_rate(self) -> float:
        """Get current success rate (last 100 requests)."""
        with self._lock:
            if not self.success_rates:
                return 0.0
            return sum(self.success_rates) / len(self.success_rates)
    
    def get_average_response_time(self) -> float:
        """Get average response time (last 100 requests)."""
        with self._lock:
            if not self.response_times:
                return 0.0
            return sum(self.response_times) / len(self.response_times)
    
    def should_alert(self) -> Tuple[bool, str]:
        """Check if alert should be triggered."""
        success_rate = self.get_current_success_rate()
        avg_response_time = self.get_average_response_time()
        error_rate = 1 - success_rate
        
        alerts = []
        
        if success_rate < self.success_rate_threshold:
            alerts.append(f"Low success rate: {success_rate:.2%}")
        
        if avg_response_time > self.response_time_threshold:
            alerts.append(f"High response time: {avg_response_time:.1f}s")
        
        if error_rate > self.error_rate_threshold:
            alerts.append(f"High error rate: {error_rate:.2%}")
        
        if alerts:
            return True, "; ".join(alerts)
        
        return False, ""
    
    def get_stats(self) -> Dict:
        """Get comprehensive monitoring statistics."""
        with self._lock:
            return {
                'total_requests': self.metrics['total_requests'],
                'successful_requests': self.metrics['successful_requests'],
                'failed_requests': self.metrics['failed_requests'],
                'current_success_rate': self.get_current_success_rate(),
                'average_response_time': self.get_average_response_time(),
                'top_errors': dict(sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
                'health_status': 'healthy' if self.get_current_success_rate() > 0.7 else 'degraded'
            }


class SessionOptimizer:
    """Optimize HTTP session for anti-detection."""
    
    def __init__(self):
        self.ua_rotator = UserAgentRotator()
        self.header_generator = HeaderGenerator()
        self.render_optimizer = RenderOptimizer()
    
    def create_optimized_session(self) -> requests.Session:
        """Create optimized session with anti-detection features."""
        session = requests.Session()
        
        # Get optimized configuration
        config = self.render_optimizer.get_optimized_session_config()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=config['max_retries'],
            backoff_factor=config['backoff_factor'],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        # Configure adapter
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=config['pool_connections'],
            pool_maxsize=config['pool_maxsize']
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set realistic headers
        user_agent = self.ua_rotator.get_next_user_agent()
        headers = self.header_generator.generate_headers(user_agent)
        session.headers.update(headers)
        
        # Configure timeout
        self.timeout = config['timeout']
        
        # Configure SSL context for better fingerprinting
        session.verify = config['verify']
        
        return session


class AntiDetectionManager:
    """Main anti-detection management class."""
    
    def __init__(self):
        self.session_optimizer = SessionOptimizer()
        self.timing_manager = TimingManager()
        self.monitor = ProductionMonitor()
        self.render_optimizer = RenderOptimizer()
        
        # Session pool for rotation
        self.sessions = []
        self.session_index = 0
        self.max_sessions = 3
        
        self._initialize_sessions()
        
        logger.info("AntiDetectionManager initialized with production hardening")
    
    def _initialize_sessions(self):
        """Initialize session pool."""
        for i in range(self.max_sessions):
            session = self.session_optimizer.create_optimized_session()
            self.sessions.append(session)
    
    def get_session(self) -> requests.Session:
        """Get optimized session from pool."""
        session = self.sessions[self.session_index]
        self.session_index = (self.session_index + 1) % self.max_sessions
        return session
    
    def refresh_session(self, session: requests.Session):
        """Refresh compromised session."""
        try:
            index = self.sessions.index(session)
            self.sessions[index] = self.session_optimizer.create_optimized_session()
            logger.info(f"Refreshed session at index {index}")
        except ValueError:
            logger.warning("Attempted to refresh session not in pool")
    
    def execute_request(self, url: str, params: Optional[Dict] = None, 
                       is_retry: bool = False, failure_count: int = 0) -> requests.Response:
        """Execute request with full anti-detection."""
        
        # Wait appropriate time
        self.timing_manager.wait_if_needed(is_retry, failure_count)
        
        # Get optimized session
        session = self.get_session()
        
        # Add request-specific randomization
        if params:
            # Add random parameter order to avoid fingerprinting
            params = dict(sorted(params.items(), key=lambda x: random.random()))
        
        start_time = time.time()
        
        try:
            # Execute request with timeout
            response = session.get(
                url, 
                params=params,
                timeout=self.session_optimizer.timeout,
                allow_redirects=True
            )
            
            response_time = time.time() - start_time
            
            # Check for success
            if response.status_code == 200:
                self.monitor.record_request(True, response_time)
                logger.debug(f"Request successful in {response_time:.2f}s")
                return response
            else:
                self.monitor.record_request(False, response_time, f"HTTP_{response.status_code}")
                logger.warning(f"Request failed with status {response.status_code}")
                
                # Refresh session if blocked
                if response.status_code in [403, 429]:
                    self.refresh_session(session)
                
                response.raise_for_status()
        
        except Exception as e:
            response_time = time.time() - start_time
            error_type = type(e).__name__
            
            self.monitor.record_request(False, response_time, error_type)
            logger.error(f"Request failed: {e}")
            
            # Refresh session on network errors
            if 'Connection' in str(e) or 'Timeout' in str(e):
                self.refresh_session(session)
            
            raise
    
    def get_stats(self) -> Dict:
        """Get anti-detection statistics."""
        base_stats = self.monitor.get_stats()
        
        # Add additional context
        base_stats.update({
            'render_environment': self.render_optimizer.render_detected,
            'active_sessions': len(self.sessions),
            'timing_mode': 'adaptive',
            'anti_detection_active': True
        })
        
        # Check for alerts
        should_alert, alert_message = self.monitor.should_alert()
        if should_alert:
            logger.warning(f"Production alert: {alert_message}")
            base_stats['alert'] = alert_message
        
        return base_stats


# Global instance
anti_detection_manager = AntiDetectionManager()