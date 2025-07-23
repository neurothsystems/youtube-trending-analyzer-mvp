// API Response Types for YouTube Trending Analyzer MVP

export interface TrendingVideo {
  rank: number;
  video_id: string;
  title: string;
  channel: string;
  channel_country: string;
  views: number;
  views_in_timeframe: number;
  likes: number;
  comments: number;
  trending_score: number;
  country_relevance_score: number;
  is_in_trending_feed: boolean;
  reasoning: string;
  url: string;
  thumbnail: string;
  upload_date: string | null;
  age_hours: number;
  engagement_rate: number;
}

export interface TrendingResponse {
  success: boolean;
  query: string;
  country: string;
  timeframe: string;
  algorithm: string;
  processing_time_ms: number;
  results: TrendingVideo[];
  metadata: {
    total_analyzed: number;
    llm_analyzed: number;
    cache_hit: boolean;
    trending_feed_matches?: number;
    llm_cost_cents?: number;
    timestamp?: string;
    message?: string;
  };
  error?: string;
}

export interface TrendingFeedVideo {
  video_id: string;
  title: string;
  channel_name: string;
  channel_id: string;
  description: string;
  upload_date: string;
  thumbnail_url: string;
  views: number;
  likes: number;
  comments: number;
  duration: number;
  trending_rank: number;
  category: string;
  tags: string[];
}

export interface TrendingFeedResponse {
  success: boolean;
  country: string;
  country_name: string;
  total_videos: number;
  trending_videos: TrendingFeedVideo[];
  fresh_only: boolean;
  note: string;
}

export interface SearchTermsResponse {
  success: boolean;
  original_query: string;
  country: string;
  country_name: string;
  expanded_terms: string[];
  total_terms: number;
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    [key: string]: {
      status: 'healthy' | 'degraded' | 'unhealthy';
      message: string;
      error?: string;
      [key: string]: any;
    };
  };
  timestamp: string;
  version: string;
  environment: string;
  message: string;
}

export interface CountryAnalytics {
  success: boolean;
  country: string;
  country_name: string;
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
  };
  video_statistics: {
    total_videos_analyzed: number;
    average_relevance_score: number;
    high_relevance_count: number;
    high_relevance_percentage: number;
  };
  trending_feed_statistics: {
    trending_feed_entries: number;
    trending_matches: number;
    match_rate_percentage: number;
  };
  llm_performance: {
    average_confidence_score: number;
    model_used: string;
  };
  popular_queries: Array<{
    query: string;
    search_count: number;
  }>;
  top_videos: Array<{
    video_id: string;
    title: string;
    channel_name: string;
    relevance_score: number;
    reasoning: string;
    views: number;
    analyzed_at: string;
  }>;
}

export interface SystemAnalytics {
  success: boolean;
  system_info: {
    service_name: string;
    version: string;
    algorithm: string;
    environment: string;
  };
  analysis_period: {
    days: number;
    start_date: string;
    end_date: string;
  };
  api_usage: {
    total_searches: number;
    unique_queries: number;
    searches_per_day: number;
  };
  cache_performance: {
    status: string;
    hits: number;
    misses: number;
    hit_rate: number;
    hit_rate_percentage: number;
    target_hit_rate: number;
    memory_used: string;
    connected_clients: number;
  };
  llm_usage: {
    daily_cost_eur: number;
    monthly_cost_eur: number;
    monthly_budget_eur: number;
    budget_remaining_eur: number;
    budget_used_percentage: number;
    estimated_tokens_processed: number;
    cost_per_million_tokens: number;
    batch_size: number;
  };
  database_statistics: {
    total_videos: number;
    total_country_analyses: number;
    total_trending_entries: number;
    recent_videos_added: number;
    recent_analyses_performed: number;
  };
  country_statistics: Array<{
    country: string;
    country_name: string;
    analysis_count: number;
    average_relevance_score: number;
  }>;
  performance_targets: {
    response_time_target_ms: number;
    cache_hit_rate_target: number;
    monthly_budget_eur: number;
  };
}

export interface BudgetAnalytics {
  success: boolean;
  budget_status: 'healthy' | 'caution' | 'warning' | 'critical';
  budget_message: string;
  cost_breakdown: {
    daily_cost_eur: number;
    monthly_cost_eur: number;
    monthly_budget_eur: number;
    budget_remaining_eur: number;
    budget_used_percentage: number;
    estimated_tokens_processed: number;
    cost_per_million_tokens: number;
    batch_size: number;
  };
  infrastructure_costs: {
    render_monthly_usd: number;
    vercel_monthly_usd: number;
    github_monthly_usd: number;
    total_infrastructure_monthly_usd: number;
  };
  cache_optimization: {
    current_hit_rate_percentage: number;
    target_hit_rate_percentage: number;
    cache_status: 'optimal' | 'needs_improvement';
    estimated_cost_savings_eur: number;
  };
  api_quotas: {
    youtube_api: {
      daily_quota: number;
      cost_per_search: number;
      cost_per_video_details: number;
      estimated_daily_usage: string;
    };
    gemini_flash: {
      cost_per_million_tokens: number;
      monthly_token_budget: number;
      estimated_videos_per_day: number;
    };
  };
  recommendations: Array<{
    type: string;
    priority: 'high' | 'medium' | 'low';
    message: string;
    action: string;
  }>;
  next_review_date: string;
}

// Form and UI types
export type CountryCode = 'DE' | 'US' | 'FR' | 'JP';
export type TimeframeOption = '24h' | '48h' | '7d';

export interface SearchFormData {
  query: string;
  country: CountryCode;
  timeframe: TimeframeOption;
  limit: number;
}

export interface Country {
  code: CountryCode;
  name: string;
  flag: string;
}

export interface TimeframeInfo {
  value: TimeframeOption;
  label: string;
  description: string;
}

// Error types
export interface ApiError {
  message: string;
  status: number;
  detail?: string;
}

export class TrendingAnalysisError extends Error {
  constructor(
    message: string,
    public status: number = 500,
    public detail?: string
  ) {
    super(message);
    this.name = 'TrendingAnalysisError';
  }
}