'use client';

import { useState } from 'react';
import { TrendingUp } from 'lucide-react';
import toast from 'react-hot-toast';
import Header from 'components/Header';
import SearchForm from 'components/SearchForm';
import ResultsDisplay from 'components/ResultsDisplay';
import { TrendingAnalyzerAPI } from 'lib/api';
import { SearchFormData, TrendingResponse, TrendingAnalysisError } from 'types/api';
import { APP_CONFIG } from 'lib/constants';

export default function HomePage() {
  const [results, setResults] = useState<TrendingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (formData: SearchFormData) => {
    setIsLoading(true);
    setResults(null);

    try {
      const response = await TrendingAnalyzerAPI.analyzeTrending(formData);
      setResults(response);
      
      if (response.success && response.results.length > 0) {
        toast.success(`Found ${response.results.length} trending videos!`);
      } else {
        toast.error('No results found. Try different search terms.');
      }
    } catch (error) {
      console.error('Search error:', error);
      
      let errorMessage = 'Failed to analyze trending videos';
      if (error instanceof TrendingAnalysisError) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
      setResults({
        success: false,
        query: formData.query,
        country: formData.country,
        timeframe: formData.timeframe,
        algorithm: APP_CONFIG.algorithm,
        processing_time_ms: 0,
        results: [],
        metadata: {
          total_analyzed: 0,
          llm_analyzed: 0,
          cache_hit: false,
          trending_feed_matches: 0,
          llm_cost_cents: 0
        },
        error: errorMessage
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (results && !results.success) {
      handleSearch({
        query: results.query,
        country: results.country as any,
        timeframe: results.timeframe as any,
        limit: 10
      });
    }
  };

  const handleCacheCleared = () => {
    // Reset results to force fresh search
    if (results) {
      toast.success('Cache cleared! Next search will use fresh data.');
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8 space-y-12">
        {/* Hero Section */}
        {!results && (
          <div className="text-center space-y-8 max-w-4xl mx-auto">
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="p-3 bg-gradient-to-r from-red-500 to-red-600 rounded-full">
                  <TrendingUp className="w-8 h-8 text-white" />
                </div>
              </div>
              <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 text-balance">
                YouTube Trending Analyzer 
                <span className="gradient-text block">MVP</span>
              </h1>
              <p className="text-xl text-gray-600 text-balance max-w-3xl mx-auto">
                Discover genuine regional YouTube trends with AI-powered country relevance analysis. 
                Find videos that are truly trending in specific countries, not just available there.
              </p>
            </div>
          </div>
        )}

        {/* Search Form */}
        <div className="max-w-4xl mx-auto">
          <SearchForm 
            onSearch={handleSearch} 
            isLoading={isLoading} 
            onCacheCleared={handleCacheCleared}
          />
        </div>

        {/* Results */}
        {results && (
          <div className="animate-fade-in-up">
            <ResultsDisplay results={results} onRetry={handleRetry} />
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
          <p>
            YouTube Trending Analyzer MVP • Built with Next.js, FastAPI, and Gemini Flash
          </p>
        </div>
      </footer>
    </div>
  );
}