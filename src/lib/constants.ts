import { Country, TimeframeInfo, CountryCode, TimeframeOption } from 'types/api';

// Supported countries with English names and flag emojis
export const COUNTRIES: Country[] = [
  { code: 'DE', name: 'Germany', flag: '🇩🇪' },
  { code: 'US', name: 'USA', flag: '🇺🇸' },
  { code: 'FR', name: 'France', flag: '🇫🇷' },
  { code: 'JP', name: 'Japan', flag: '🇯🇵' }
];

// Timeframe options with descriptions
export const TIMEFRAMES: TimeframeInfo[] = [
  { 
    value: '24h', 
    label: '24 hours', 
    description: 'Videos trending in the last day' 
  },
  { 
    value: '48h', 
    label: '48 hours', 
    description: 'Videos trending in the last 2 days' 
  },
  { 
    value: '7d', 
    label: '7 days', 
    description: 'Videos trending in the last week' 
  }
];

// Default form values
export const DEFAULT_FORM_VALUES = {
  query: '',
  country: (process.env.NEXT_PUBLIC_DEFAULT_COUNTRY as CountryCode) || 'US',
  timeframe: (process.env.NEXT_PUBLIC_DEFAULT_TIMEFRAME as TimeframeOption) || '48h',
  limit: parseInt(process.env.NEXT_PUBLIC_DEFAULT_LIMIT || '10')
};

// API endpoints
export const API_ENDPOINTS = {
  trending: '/api/mvp/trending',
  trendingFeeds: '/api/mvp/trending/feeds',
  searchTerms: '/api/mvp/trending/search-terms',
  health: '/api/mvp/health',
  analytics: {
    country: '/api/mvp/analytics/country',
    system: '/api/mvp/analytics/system',
    budget: '/api/mvp/analytics/budget'
  },
  googleTrends: {
    trends: '/api/mvp/google-trends',
    validation: '/api/mvp/google-trends/validation',
    related: '/api/mvp/google-trends/related',
    status: '/api/mvp/google-trends/status'
  },
  cache: {
    stats: '/api/mvp/trending/cache/stats',
    invalidate: '/api/mvp/trending/cache/invalidate'
  }
} as const;

// YouTube categories (for display purposes)
export const YOUTUBE_CATEGORIES = {
  '1': 'Film & Animation',
  '2': 'Autos & Vehicles', 
  '10': 'Music',
  '15': 'Pets & Animals',
  '17': 'Sports',
  '19': 'Travel & Events',
  '20': 'Gaming',
  '22': 'People & Blogs',
  '23': 'Comedy',
  '24': 'Entertainment',
  '25': 'News & Politics',
  '26': 'Howto & Style',
  '27': 'Education',
  '28': 'Science & Technology'
} as const;

// Trending score thresholds for visual indication
export const TRENDING_SCORE_THRESHOLDS = {
  EXCELLENT: 8000,  // Green
  GOOD: 5000,       // Blue
  MODERATE: 2000,   // Yellow
  LOW: 500          // Orange
  // Below LOW = Red
} as const;

// Country relevance score thresholds
export const RELEVANCE_SCORE_THRESHOLDS = {
  VERY_HIGH: 0.9,   // Excellent relevance
  HIGH: 0.7,        // Good relevance
  MODERATE: 0.5,    // Moderate relevance
  LOW: 0.3          // Low relevance
  // Below LOW = Very Low
} as const;

// Color schemes for different metrics
export const COLORS = {
  trending: {
    excellent: '#10b981', // green-500
    good: '#3b82f6',      // blue-500
    moderate: '#f59e0b',  // amber-500
    low: '#f97316',       // orange-500
    poor: '#ef4444'       // red-500
  },
  relevance: {
    veryHigh: '#059669',  // emerald-600
    high: '#0d9488',      // teal-600
    moderate: '#0891b2',  // cyan-600
    low: '#0284c7',       // sky-600
    veryLow: '#6366f1'    // indigo-500
  },
  status: {
    healthy: '#10b981',   // green-500
    warning: '#f59e0b',   // amber-500
    critical: '#ef4444',  // red-500
    unknown: '#6b7280'    // gray-500
  }
} as const;

// Application metadata
export const APP_CONFIG = {
  name: process.env.NEXT_PUBLIC_APP_NAME || 'YouTube Trending Analyzer MVP',
  version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  description: process.env.NEXT_PUBLIC_SITE_DESCRIPTION || 'LLM-powered platform for genuine regional YouTube trend analysis',
  algorithm: 'MVP-LLM-Enhanced',
  supportedCountries: ['DE', 'US', 'FR', 'JP'],
  maxResponseTime: 5000, // 5 seconds
  cacheTimeout: parseInt(process.env.NEXT_PUBLIC_CACHE_TIMEOUT || '300000') // 5 minutes
} as const;

// Performance targets
export const PERFORMANCE_TARGETS = {
  responseTime: 5000,     // milliseconds
  cacheHitRate: 70,       // percentage
  monthlyBudget: 50       // EUR
} as const;

// Example search queries for different countries
export const EXAMPLE_QUERIES = {
  DE: ['KI', 'Fußball', 'Musik', 'Gaming', 'Tech'],
  US: ['AI', 'Football', 'Music', 'Gaming', 'Tech'],
  FR: ['IA', 'Football', 'Musique', 'Gaming', 'Tech'],
  JP: ['AI', 'アニメ', '音楽', 'ゲーム', 'テック']
} as const;

// UI constants
export const UI_CONSTANTS = {
  maxQueryLength: 100,
  minQueryLength: 2,
  defaultResultLimit: 10,
  maxResultLimit: 50,
  debounceDelay: 500,     // milliseconds for search input
  animationDelay: 150,    // milliseconds between card animations
  toastDuration: 4000     // milliseconds for toast notifications
} as const;