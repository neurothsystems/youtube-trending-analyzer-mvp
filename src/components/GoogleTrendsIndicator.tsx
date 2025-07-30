'use client';

import { TrendingUp, TrendingDown, Activity, Globe } from 'lucide-react';
import { GoogleTrendsData } from 'types/api';

interface GoogleTrendsIndicatorProps {
  googleTrends: GoogleTrendsData;
  className?: string;
}

export default function GoogleTrendsIndicator({ googleTrends, className = '' }: GoogleTrendsIndicatorProps) {
  const getPlatformAlignmentColor = (alignment: string) => {
    switch (alignment) {
      case 'strong': return 'text-green-600 bg-green-100';
      case 'moderate': return 'text-blue-600 bg-blue-100';
      case 'weak': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getPlatformAlignmentIcon = (alignment: string, isGoogleTrending: boolean) => {
    if (alignment === 'strong') {
      return <TrendingUp className="w-3 h-3" />;
    } else if (isGoogleTrending) {
      return <Activity className="w-3 h-3" />;
    } else {
      return <Globe className="w-3 h-3" />;
    }
  };

  const getTrendingScoreColor = (score: number) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.5) return 'text-blue-600';
    if (score >= 0.3) return 'text-yellow-600';
    return 'text-gray-600';
  };

  if (googleTrends.error) {
    return (
      <div className={`inline-flex items-center space-x-1 text-xs text-gray-500 ${className}`}>
        <Globe className="w-3 h-3" />
        <span>Google Trends: Error</span>
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center space-x-2 ${className}`}>
      {/* Google Trends Score */}
      <span className={`inline-flex items-center space-x-1 text-xs ${getTrendingScoreColor(googleTrends.trend_score)}`}>
        <Globe className="w-3 h-3" />
        <span>{(googleTrends.trend_score * 100).toFixed(0)}%</span>
      </span>

      {/* Cross-Platform Validation */}
      {googleTrends.platform_alignment !== 'none' && (
        <span className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${getPlatformAlignmentColor(googleTrends.platform_alignment)}`}>
          {getPlatformAlignmentIcon(googleTrends.platform_alignment, googleTrends.is_trending)}
          <span className="capitalize">{googleTrends.platform_alignment}</span>
        </span>
      )}

      {/* Cache Hit Indicator */}
      {googleTrends.cache_hit && (
        <span className="text-xs text-gray-400">📦</span>
      )}
    </div>
  );
}