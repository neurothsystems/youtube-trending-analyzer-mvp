'use client';

import { Info, Search, TrendingUp, Database, Filter } from 'lucide-react';
import { TrendingResponse } from 'types/api';
import { cn } from 'lib/utils';

interface SearchTransparencyProps {
  data: TrendingResponse;
  className?: string;
}

export default function SearchTransparency({ data, className }: SearchTransparencyProps) {
  const { metadata } = data;
  const searchTerms = metadata.search_terms_used;
  const collectionStats = metadata.collection_stats;

  if (!searchTerms && !collectionStats) {
    return null;
  }

  return (
    <div className={cn("bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center space-x-2">
        <Info className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold text-blue-900">Search Transparency</h3>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Search Terms Used */}
        {searchTerms && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Search className="w-4 h-4 text-blue-600" />
              <h4 className="font-medium text-blue-800">Search Terms Used</h4>
              <span className="text-xs bg-blue-200 text-blue-700 px-2 py-1 rounded-full">
                {searchTerms.total_search_terms || 0} terms
              </span>
            </div>

            <div className="space-y-2">
              {/* Tier 1 - Original & Expanded */}
              {searchTerms.tier_1_terms && searchTerms.tier_1_terms.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-blue-700 mb-1">
                    Tier 1: Original & Expanded
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {searchTerms.tier_1_terms.map((term, index) => (
                      <span
                        key={index}
                        className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded"
                      >
                        {term}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Tier 2 - Category Terms */}
              {searchTerms.tier_2_terms && searchTerms.tier_2_terms.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-blue-700 mb-1">
                    Tier 2: Category Terms
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {searchTerms.tier_2_terms.map((term, index) => (
                      <span
                        key={index}
                        className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded"
                      >
                        {term}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Tier 3 - Generic Trending */}
              {searchTerms.tier_3_terms && searchTerms.tier_3_terms.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-blue-700 mb-1">
                    Tier 3: Generic Trending
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {searchTerms.tier_3_terms.map((term, index) => (
                      <span
                        key={index}
                        className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded"
                      >
                        {term}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Collection Statistics */}
        {collectionStats && (
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Database className="w-4 h-4 text-blue-600" />
              <h4 className="font-medium text-blue-800">Collection Statistics</h4>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {/* Videos from Search */}
              <div className="bg-white rounded-lg p-3 border border-blue-100">
                <div className="flex items-center space-x-2">
                  <Search className="w-3 h-3 text-gray-500" />
                  <span className="text-xs text-gray-600">From Search</span>
                </div>
                <div className="text-lg font-semibold text-gray-900">
                  {collectionStats.videos_from_search || 0}
                </div>
              </div>

              {/* Videos from Trending Feed */}
              <div className="bg-white rounded-lg p-3 border border-blue-100">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-3 h-3 text-gray-500" />
                  <span className="text-xs text-gray-600">From Trending</span>
                </div>
                <div className="text-lg font-semibold text-gray-900">
                  {collectionStats.videos_from_trending_feed || 0}
                </div>
              </div>

              {/* Total Collected */}
              <div className="bg-white rounded-lg p-3 border border-blue-100">
                <div className="flex items-center space-x-2">
                  <Database className="w-3 h-3 text-gray-500" />
                  <span className="text-xs text-gray-600">Total Collected</span>
                </div>
                <div className="text-lg font-semibold text-gray-900">
                  {collectionStats.total_collected || 0}
                </div>
              </div>

              {/* Duplicates Removed */}
              <div className="bg-white rounded-lg p-3 border border-blue-100">
                <div className="flex items-center space-x-2">
                  <Filter className="w-3 h-3 text-gray-500" />
                  <span className="text-xs text-gray-600">Duplicates Removed</span>
                </div>
                <div className="text-lg font-semibold text-gray-900">
                  {collectionStats.duplicates_removed || 0}
                </div>
              </div>
            </div>

            {/* Processing Summary */}
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="text-xs text-gray-600 mb-1">Processing Summary</div>
              <div className="text-sm text-gray-800">
                Analyzed <strong>{metadata.total_analyzed}</strong> videos, 
                {' '}processed <strong>{metadata.llm_analyzed}</strong> with AI,
                {' '}found <strong>{data.results.length}</strong> relevant results
                {metadata.trending_feed_matches && metadata.trending_feed_matches > 0 && (
                  <span> (including <strong>{metadata.trending_feed_matches}</strong> from trending feeds)</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="border-t border-blue-200 pt-3">
        <div className="text-xs text-blue-600 mb-2">Search Strategy:</div>
        <div className="flex flex-wrap gap-4 text-xs text-blue-700">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-green-100 rounded"></div>
            <span>Original + Expanded terms</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-yellow-100 rounded"></div>
            <span>Category-specific terms</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-purple-100 rounded"></div>
            <span>Generic trending terms</span>
          </div>
        </div>
      </div>
    </div>
  );
}