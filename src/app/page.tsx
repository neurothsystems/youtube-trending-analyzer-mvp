'use client';

import { useState } from 'react';
import { Sparkles, Brain, Globe, Zap, TrendingUp, CheckCircle } from 'lucide-react';
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
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

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
              <div className="card p-6 text-center hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">AI-Powered Analysis</h3>
                <p className="text-sm text-gray-600">
                  Gemini Flash LLM analyzes cultural relevance and regional context
                </p>
              </div>

              <div className="card p-6 text-center hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Globe className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Multi-Country</h3>
                <p className="text-sm text-gray-600">
                  Support for Germany, USA, France, and Japan with localized analysis
                </p>
              </div>

              <div className="card p-6 text-center hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">MOMENTUM Algorithm</h3>
                <p className="text-sm text-gray-600">
                  Advanced trending score combining views, engagement, and relevance
                </p>
              </div>

              <div className="card p-6 text-center hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-6 h-6 text-yellow-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Real-time Data</h3>
                <p className="text-sm text-gray-600">
                  Fresh analysis with official YouTube trending feed validation
                </p>
              </div>
            </div>

            {/* How it Works */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">How It Works</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center mx-auto mb-4 font-bold">
                    1
                  </div>
                  <h3 className="font-semibold mb-2">Search & Collect</h3>
                  <p className="text-sm text-gray-600">
                    We search YouTube with country-specific queries and collect video metadata
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center mx-auto mb-4 font-bold">
                    2
                  </div>
                  <h3 className="font-semibold mb-2">AI Analysis</h3>
                  <p className="text-sm text-gray-600">
                    Gemini Flash analyzes cultural relevance, language, and regional context
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center mx-auto mb-4 font-bold">
                    3
                  </div>
                  <h3 className="font-semibold mb-2">Smart Ranking</h3>
                  <p className="text-sm text-gray-600">
                    MOMENTUM algorithm ranks videos by true regional trending potential
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Search Form */}
        <div className="max-w-4xl mx-auto">
          <SearchForm onSearch={handleSearch} isLoading={isLoading} />
        </div>

        {/* Results */}
        {results && (
          <div className="animate-fade-in-up">
            <ResultsDisplay results={results} onRetry={handleRetry} />
          </div>
        )}

        {/* Technical Info */}
        {!results && (
          <div className="max-w-4xl mx-auto">
            <div className="card p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
                Advanced Trending Analysis
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center space-x-2">
                    <Sparkles className="w-5 h-5 text-blue-500" />
                    <span>What Makes Us Different</span>
                  </h3>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>Distinguishes between "available in country" vs "trending in country"</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>AI analyzes cultural context, language patterns, and creator origin</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>Combines multiple data sources for comprehensive analysis</span>
                    </li>
                    <li className="flex items-start space-x-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>Budget-optimized with intelligent caching (€50/month)</span>
                    </li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-900 mb-3 flex items-center space-x-2">
                    <Brain className="w-5 h-5 text-purple-500" />
                    <span>Technical Specifications</span>
                  </h3>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li><strong>Algorithm:</strong> {APP_CONFIG.algorithm}</li>
                    <li><strong>LLM:</strong> Google Gemini Flash</li>
                    <li><strong>Response Time:</strong> &lt;5 seconds target</li>
                    <li><strong>Countries:</strong> DE, US, FR, JP</li>
                    <li><strong>Timeframes:</strong> 24h, 48h, 7d</li>
                    <li><strong>Data Sources:</strong> YouTube API + Trending Feeds</li>
                    <li><strong>Caching:</strong> Redis with 2h TTL</li>
                    <li><strong>Version:</strong> {APP_CONFIG.version}</li>
                  </ul>
                </div>
              </div>
            </div>
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