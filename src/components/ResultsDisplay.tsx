'use client';

import { useState } from 'react';
import { Clock, BarChart3, Brain, Eye, TrendingUp, Award, Filter, Grid, List } from 'lucide-react';
import { TrendingResponse } from 'types/api';
import { 
  formatNumber, 
  formatCurrency, 
  getCountryInfo, 
  getTimeframeInfo,
  formatRelativeTime,
  cn
} from 'lib/utils';
import VideoCard from './VideoCard';

interface ResultsDisplayProps {
  results: TrendingResponse;
  onRetry?: () => void;
}

type ViewMode = 'grid' | 'list';
type SortMode = 'rank' | 'trending_score' | 'relevance' | 'views' | 'engagement';

export default function ResultsDisplay({ results, onRetry }: ResultsDisplayProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [sortMode, setSortMode] = useState<SortMode>('rank');
  
  if (!results.success) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Analysis Failed</h3>
          <p className="text-gray-600 mb-4">
            {results.error || 'An error occurred while analyzing trending videos.'}
          </p>
          {onRetry && (
            <button onClick={onRetry} className="btn-primary">
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  const sortedResults = [...results.results].sort((a, b) => {
    switch (sortMode) {
      case 'trending_score':
        return b.trending_score - a.trending_score;
      case 'relevance':
        return b.country_relevance_score - a.country_relevance_score;
      case 'views':
        return b.views - a.views;
      case 'engagement':
        return b.engagement_rate - a.engagement_rate;
      default:
        return a.rank - b.rank;
    }
  });

  const countryInfo = getCountryInfo(results.country as any);
  const timeframeInfo = getTimeframeInfo(results.timeframe as any);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Results Header */}
      <div className="card p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between space-y-4 lg:space-y-0">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Trending Results for "{results.query}"
            </h2>
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center space-x-1">
                <span className="text-lg">{countryInfo.flag}</span>
                <span>Country: {countryInfo.name}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>Timeframe: {timeframeInfo.label}</span>
              </div>
              <div className="flex items-center space-x-1">
                <BarChart3 className="w-4 h-4" />
                <span>Algorithm: {results.algorithm}</span>
              </div>
            </div>
          </div>

          {/* View Controls */}
          <div className="flex items-center space-x-2">
            <div className="flex rounded-lg border border-gray-300 overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={cn(
                  'px-3 py-2 text-sm transition-colors',
                  viewMode === 'grid' 
                    ? 'bg-primary-500 text-white' 
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                )}
              >
                <Grid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={cn(
                  'px-3 py-2 text-sm transition-colors',
                  viewMode === 'list' 
                    ? 'bg-primary-500 text-white' 
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                )}
              >
                <List className="w-4 h-4" />
              </button>
            </div>

            <select
              value={sortMode}
              onChange={(e) => setSortMode(e.target.value as SortMode)}
              className="select text-sm"
            >
              <option value="rank">Sort by Rank</option>
              <option value="trending_score">Sort by Trending Score</option>
              <option value="relevance">Sort by Relevance</option>
              <option value="views">Sort by Views</option>
              <option value="engagement">Sort by Engagement</option>
            </select>
          </div>
        </div>
      </div>

      {/* Metadata Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="card p-4 text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <Eye className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{results.results.length}</p>
          <p className="text-sm text-gray-600">Results Found</p>
        </div>

        <div className="card p-4 text-center">
          <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <BarChart3 className="w-5 h-5 text-green-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{formatNumber(results.metadata.total_analyzed)}</p>
          <p className="text-sm text-gray-600">Videos Analyzed</p>
        </div>

        <div className="card p-4 text-center">
          <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <Brain className="w-5 h-5 text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{formatNumber(results.metadata.llm_analyzed)}</p>
          <p className="text-sm text-gray-600">AI Analyzed</p>
        </div>

        <div className="card p-4 text-center">
          <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <Award className="w-5 h-5 text-red-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{results.metadata.trending_feed_matches || 0}</p>
          <p className="text-sm text-gray-600">In Trending Feed</p>
        </div>

        <div className="card p-4 text-center">
          <div className="w-10 h-10 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <Clock className="w-5 h-5 text-yellow-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{((results.processing_time_ms || 0) / 1000).toFixed(1)}s</p>
          <p className="text-sm text-gray-600">Processing Time</p>
        </div>
      </div>

      {/* Cache and Cost Info */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center justify-between gap-4 text-sm text-gray-600">
          <div className="flex items-center space-x-4">
            <span className={`px-2 py-1 rounded-full text-xs ${
              results.metadata.cache_hit ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
            }`}>
              {results.metadata.cache_hit ? 'Cache Hit' : 'Fresh Analysis'}
            </span>
            
            {results.metadata.llm_cost_cents && results.metadata.llm_cost_cents > 0 && (
              <span>
                LLM Cost: {formatCurrency(results.metadata.llm_cost_cents / 100)}
              </span>
            )}
          </div>

          <div className="text-right">
            <p className="text-xs text-gray-500">
              Analysis completed at {new Date().toLocaleTimeString()}
            </p>
          </div>
        </div>
      </div>

      {/* Results Grid/List */}
      {results.results.length > 0 ? (
        <div className={cn(
          'grid gap-6',
          viewMode === 'grid' 
            ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3' 
            : 'grid-cols-1'
        )}>
          {sortedResults.map((video, index) => (
            <VideoCard
              key={video.video_id}
              video={video}
              index={index}
            />
          ))}
        </div>
      ) : (
        <div className="card p-8 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Results Found</h3>
          <p className="text-gray-600 mb-4">
            No trending videos were found for your search criteria. Try adjusting your search terms or selecting a different timeframe.
          </p>
          {results.metadata.message && (
            <p className="text-sm text-gray-500 italic">
              {results.metadata.message}
            </p>
          )}
        </div>
      )}

      {/* Analysis Details (Expandable) */}
      <details className="card p-6">
        <summary className="cursor-pointer font-medium text-gray-900 mb-4">
          Analysis Details & Methodology
        </summary>
        <div className="space-y-4 text-sm text-gray-600">
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">MOMENTUM MVP Algorithm</h4>
            <p>
              Our advanced trending algorithm combines video momentum (views/hour + engagement rate), 
              country relevance scoring via Gemini Flash LLM, and trending feed boost factors to identify 
              videos that are genuinely trending in specific regions.
            </p>
          </div>
          
          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Country Relevance Analysis</h4>
            <p>
              Each video is analyzed by AI to determine cultural relevance, language patterns, 
              creator geography, and audience engagement specific to {countryInfo.name}. 
              This ensures results show videos truly trending in the selected country, 
              not just available there.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">Data Sources</h4>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>YouTube Search API with region-specific queries</li>
              <li>Official YouTube Trending Feeds</li>
              <li>Video metadata and engagement statistics</li>
              <li>AI-powered content and cultural analysis</li>
            </ul>
          </div>
        </div>
      </details>
    </div>
  );
}