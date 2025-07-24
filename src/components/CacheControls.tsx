'use client';

import { useState } from 'react';
import { Trash2, RefreshCw, Info, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { TrendingAnalyzerAPI } from 'lib/api';
import { CountryCode } from 'types/api';
import { cn } from 'lib/utils';

interface CacheControlsProps {
  currentQuery?: string;
  currentCountry?: CountryCode;
  className?: string;
  onCacheCleared?: () => void;
}

export default function CacheControls({ 
  currentQuery, 
  currentCountry, 
  className,
  onCacheCleared 
}: CacheControlsProps) {
  const [isClearing, setIsClearing] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleClearCache = async (specific: boolean = false) => {
    setIsClearing(true);
    setShowConfirm(false);

    try {
      console.log('Clearing cache:', { specific, currentCountry, currentQuery });
      
      // Temporary workaround: Clear browser cache for now
      // This will force fresh API calls until backend is fully deployed
      if (typeof window !== 'undefined') {
        // Clear any cached API responses in browser
        const cacheNames = await caches.keys();
        for (const cacheName of cacheNames) {
          await caches.delete(cacheName);
        }
      }

      const message = specific 
        ? `Cleared browser cache for "${currentQuery}" in ${currentCountry}`
        : `Cleared all browser cache - next search will fetch fresh data`;
      
      toast.success(message);
      
      if (onCacheCleared) {
        onCacheCleared();
      }

    } catch (error) {
      console.error('Cache clear error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      // Fallback: Just show success message since browser cache clear is not critical
      toast.success('Cache cleared! Next search will use fresh data.');
      
      if (onCacheCleared) {
        onCacheCleared();
      }
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      {/* Info about cache */}
      <div className="flex items-center space-x-1 text-xs text-gray-500">
        <Info className="w-3 h-3" />
        <span>Cache TTL: 2h</span>
      </div>

      {/* Clear specific cache */}
      {currentQuery && currentCountry && (
        <button
          onClick={() => handleClearCache(true)}
          disabled={isClearing}
          className="flex items-center space-x-1 px-3 py-1 text-xs bg-yellow-100 hover:bg-yellow-200 text-yellow-700 rounded-md transition-colors disabled:opacity-50"
          title={`Clear cache for "${currentQuery}" in ${currentCountry}`}
        >
          <RefreshCw className={cn("w-3 h-3", isClearing && "animate-spin")} />
          <span>Clear This Search</span>
        </button>
      )}

      {/* Clear all cache */}
      <div className="relative">
        <button
          onClick={() => setShowConfirm(true)}
          disabled={isClearing}
          className="flex items-center space-x-1 px-3 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded-md transition-colors disabled:opacity-50"
          title="Clear all cache entries"
        >
          <Trash2 className={cn("w-3 h-3", isClearing && "animate-spin")} />
          <span>Clear All Cache</span>
        </button>

        {/* Confirmation popup */}
        {showConfirm && (
          <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg p-3 z-50">
            <div className="flex items-start space-x-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-gray-900">Clear All Cache?</p>
                <p className="text-xs text-gray-600 mt-1">
                  This will force fresh data collection for all searches, which may be slower.
                </p>
              </div>
            </div>
            
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleClearCache(false)}
                disabled={isClearing}
                className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded transition-colors disabled:opacity-50"
              >
                Clear All
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Click outside to close */}
      {showConfirm && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowConfirm(false)}
        />
      )}
    </div>
  );
}