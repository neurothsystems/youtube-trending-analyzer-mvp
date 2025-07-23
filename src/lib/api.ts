import axios, { AxiosResponse } from 'axios';
import { 
  TrendingResponse, 
  TrendingFeedResponse, 
  SearchTermsResponse,
  HealthCheck,
  CountryAnalytics,
  SystemAnalytics,
  BudgetAnalytics,
  SearchFormData,
  CountryCode,
  TimeframeOption,
  ApiError,
  TrendingAnalysisError
} from 'types/api';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000'),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging and auth (if needed in future)
api.interceptors.request.use(
  (config) => {
    if (process.env.NEXT_PUBLIC_ENABLE_DEBUG === 'true') {
      console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    if (process.env.NEXT_PUBLIC_ENABLE_DEBUG === 'true') {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error);
    
    if (error.response) {
      // Server responded with error status
      const apiError: ApiError = {
        message: error.response.data?.detail || error.response.data?.message || 'Server error',
        status: error.response.status,
        detail: error.response.data?.detail
      };
      
      throw new TrendingAnalysisError(
        apiError.message,
        apiError.status,
        apiError.detail
      );
    } else if (error.request) {
      // Request was made but no response received
      throw new TrendingAnalysisError(
        'Network error - please check your connection',
        503
      );
    } else {
      // Something else happened
      throw new TrendingAnalysisError(
        error.message || 'Unknown error occurred',
        500
      );
    }
  }
);

// API Client Class
export class TrendingAnalyzerAPI {
  
  /**
   * Main trending analysis endpoint
   */
  static async analyzeTrending(params: SearchFormData): Promise<TrendingResponse> {
    try {
      const response = await api.get<TrendingResponse>('/api/mvp/trending', {
        params: {
          query: params.query,
          country: params.country,
          timeframe: params.timeframe,
          limit: params.limit
        }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error analyzing trending videos:', error);
      throw error;
    }
  }

  /**
   * Get official YouTube trending feed for a country
   */
  static async getTrendingFeed(
    country: CountryCode, 
    freshOnly: boolean = false
  ): Promise<TrendingFeedResponse> {
    try {
      const response = await api.get<TrendingFeedResponse>(`/api/mvp/trending/feeds/${country}`, {
        params: { fresh_only: freshOnly }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error fetching trending feed:', error);
      throw error;
    }
  }

  /**
   * Get expanded search terms for a query and country
   */
  static async getSearchTerms(
    query: string, 
    country: CountryCode
  ): Promise<SearchTermsResponse> {
    try {
      const response = await api.get<SearchTermsResponse>('/api/mvp/trending/search-terms', {
        params: { query, country }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error expanding search terms:', error);
      throw error;
    }
  }

  /**
   * Get system health status
   */
  static async getHealth(): Promise<HealthCheck> {
    try {
      const response = await api.get<HealthCheck>('/api/mvp/health');
      return response.data;
    } catch (error) {
      console.error('Error checking system health:', error);
      throw error;
    }
  }

  /**
   * Get country-specific analytics
   */
  static async getCountryAnalytics(
    country: CountryCode,
    days: number = 7
  ): Promise<CountryAnalytics> {
    try {
      const response = await api.get<CountryAnalytics>(`/api/mvp/analytics/country/${country}`, {
        params: { days }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error fetching country analytics:', error);
      throw error;
    }
  }

  /**
   * Get system-wide analytics
   */
  static async getSystemAnalytics(days: number = 7): Promise<SystemAnalytics> {
    try {
      const response = await api.get<SystemAnalytics>('/api/mvp/analytics/system', {
        params: { days }
      });
      
      return response.data;
    } catch (error) {
      console.error('Error fetching system analytics:', error);
      throw error;
    }
  }

  /**
   * Get budget analytics
   */
  static async getBudgetAnalytics(): Promise<BudgetAnalytics> {
    try {
      const response = await api.get<BudgetAnalytics>('/api/mvp/analytics/budget');
      return response.data;
    } catch (error) {
      console.error('Error fetching budget analytics:', error);
      throw error;
    }
  }

  /**
   * Invalidate cache (admin function)
   */
  static async invalidateCache(
    country?: CountryCode,
    query?: string
  ): Promise<{ success: boolean; message: string; entries_deleted: number }> {
    try {
      const params: Record<string, string> = {};
      if (country) params.country = country;
      if (query) params.query = query;
      
      const response = await api.post('/api/mvp/trending/cache/invalidate', null, {
        params
      });
      
      return response.data;
    } catch (error) {
      console.error('Error invalidating cache:', error);
      throw error;
    }
  }

  /**
   * Get cache statistics
   */
  static async getCacheStats(): Promise<{
    success: boolean;
    cache_stats: any;
    budget_optimization: any;
  }> {
    try {
      const response = await api.get('/api/mvp/trending/cache/stats');
      return response.data;
    } catch (error) {
      console.error('Error fetching cache stats:', error);
      throw error;
    }
  }
}

// Export the default axios instance for custom requests
export default api;