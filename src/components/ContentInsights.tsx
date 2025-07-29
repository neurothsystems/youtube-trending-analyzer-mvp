'use client';

import { useState, useEffect } from 'react';
import { BarChart3, Globe, TrendingUp, Users, PlayCircle } from 'lucide-react';

interface CountryAnalytics {
  country: string;
  country_name: string;
  total_videos: number;
  avg_relevance_score: number;
  high_relevance_count: number;
  trending_feed_count: number;
  trending_matches: number;
  popular_queries: Array<{
    query: string;
    search_count: number;
  }>;
  top_videos: Array<{
    video_id: string;
    title: string;
    channel_name: string;
    relevance_score: number;
    confidence_score: number;
  }>;
}

export default function ContentInsights() {
  const [countryData, setCountryData] = useState<CountryAnalytics[]>([]);
  const [selectedCountry, setSelectedCountry] = useState('DE');
  const [days, setDays] = useState(7);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const countries = [
    { code: 'DE', name: 'Deutschland', flag: '🇩🇪' },
    { code: 'US', name: 'USA', flag: '🇺🇸' },
    { code: 'FR', name: 'Frankreich', flag: '🇫🇷' },
    { code: 'JP', name: 'Japan', flag: '🇯🇵' }
  ];

  useEffect(() => {
    loadCountryAnalytics();
  }, [days]);

  const loadCountryAnalytics = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Load data for all countries
      const promises = countries.map(async (country) => {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/mvp/analytics/country/${country.code}?days=${days}`
        );
        
        if (!response.ok) {
          throw new Error(`Failed to load data for ${country.code}`);
        }
        
        const data = await response.json();
        return {
          ...data,
          country: country.code,
          country_name: country.name
        };
      });
      
      const results = await Promise.all(promises);
      setCountryData(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler');
      console.error('Content analytics error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedCountryData = countryData.find(c => c.country === selectedCountry);

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg p-6 shadow-sm border animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="p-2 bg-red-100 rounded-full mr-3">
            <BarChart3 className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-800">Fehler beim Laden der Content-Daten</h3>
            <p className="text-red-600 mt-1">{error}</p>
            <button 
              onClick={loadCountryAnalytics}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Erneut versuchen
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg p-4 shadow-sm border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-gray-900">Land wählen</h2>
            <div className="flex space-x-2">
              {countries.map((country) => (
                <button
                  key={country.code}
                  onClick={() => setSelectedCountry(country.code)}
                  className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedCountry === country.code
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  <span className="mr-2">{country.flag}</span>
                  {country.code}
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex space-x-2">
            {[7, 14, 30].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  days === d
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Country Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {countryData.map((country) => {
          const countryInfo = countries.find(c => c.code === country.country);
          return (
            <div 
              key={country.country}
              className={`bg-white rounded-lg p-6 shadow-sm border cursor-pointer transition-all ${
                selectedCountry === country.country ? 'ring-2 ring-blue-500' : 'hover:shadow-md'
              }`}
              onClick={() => setSelectedCountry(country.country)}
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl">{countryInfo?.flag}</span>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">
                    {country.total_videos}
                  </p>
                  <p className="text-xs text-gray-500">Videos</p>
                </div>
              </div>
              <h3 className="font-medium text-gray-900">{countryInfo?.name}</h3>
              <p className="text-sm text-gray-600 mt-1">
                Ø Score: {(country.avg_relevance_score * 100).toFixed(0)}%
              </p>
              <p className="text-sm text-blue-600 mt-1">
                {country.high_relevance_count} High-Quality
              </p>
            </div>
          );
        })}
      </div>

      {selectedCountryData && (
        <>
          {/* Selected Country Details */}
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <div className="flex items-center mb-6">
              <div className="p-2 bg-blue-100 rounded-lg mr-3">
                <Globe className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">
                {countries.find(c => c.code === selectedCountry)?.name} - Content Analyse
              </h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <div className="flex items-center mb-3">
                  <PlayCircle className="w-5 h-5 text-purple-600 mr-2" />
                  <h4 className="font-medium text-gray-700">Video Performance</h4>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Gesamt analysiert</span>
                    <span className="text-sm font-medium text-gray-900">
                      {selectedCountryData.total_videos}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">High Relevance (≥80%)</span>
                    <span className="text-sm font-medium text-green-600">
                      {selectedCountryData.high_relevance_count}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Ø Relevance Score</span>
                    <span className="text-sm font-medium text-blue-600">
                      {(selectedCountryData.avg_relevance_score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center mb-3">
                  <TrendingUp className="w-5 h-5 text-orange-600 mr-2" />
                  <h4 className="font-medium text-gray-700">Trending Feed</h4>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Trending Videos</span>
                    <span className="text-sm font-medium text-gray-900">
                      {selectedCountryData.trending_feed_count}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Matches gefunden</span>
                    <span className="text-sm font-medium text-green-600">
                      {selectedCountryData.trending_matches}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Match Rate</span>
                    <span className="text-sm font-medium text-blue-600">
                      {selectedCountryData.trending_feed_count > 0 
                        ? ((selectedCountryData.trending_matches / selectedCountryData.trending_feed_count) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <div className="flex items-center mb-3">
                  <Users className="w-5 h-5 text-indigo-600 mr-2" />
                  <h4 className="font-medium text-gray-700">User Interesse</h4>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Beliebte Queries</span>
                    <span className="text-sm font-medium text-gray-900">
                      {selectedCountryData.popular_queries?.length || 0}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Top Videos</span>
                    <span className="text-sm font-medium text-gray-900">
                      {selectedCountryData.top_videos?.length || 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Popular Queries */}
          {selectedCountryData.popular_queries && selectedCountryData.popular_queries.length > 0 && (
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h4 className="text-md font-semibold text-gray-900 mb-4">
                Beliebte Suchanfragen in {countries.find(c => c.code === selectedCountry)?.name}
              </h4>
              <div className="space-y-3">
                {selectedCountryData.popular_queries.slice(0, 8).map((query, index) => {
                  const maxCount = Math.max(...selectedCountryData.popular_queries.map(q => q.search_count));
                  const width = (query.search_count / maxCount) * 100;
                  
                  return (
                    <div key={index} className="flex items-center">
                      <div className="w-32 text-sm text-gray-700 font-medium">
                        {query.query}
                      </div>
                      <div className="flex-1 ml-4">
                        <div className="bg-gray-100 rounded-full h-4 relative">
                          <div 
                            className="bg-gradient-to-r from-blue-500 to-blue-600 h-4 rounded-full flex items-center justify-end pr-2"
                            style={{ width: `${Math.max(width, 10)}%` }}
                          >
                            <span className="text-xs text-white font-medium">
                              {query.search_count}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Top Videos */}
          {selectedCountryData.top_videos && selectedCountryData.top_videos.length > 0 && (
            <div className="bg-white rounded-lg p-6 shadow-sm border">
              <h4 className="text-md font-semibold text-gray-900 mb-4">
                Top-bewertete Videos
              </h4>
              <div className="space-y-4">
                {selectedCountryData.top_videos.slice(0, 5).map((video, index) => (
                  <div key={video.video_id} className="flex items-center p-4 border rounded-lg">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                      <span className="text-sm font-bold text-blue-600">#{index + 1}</span>
                    </div>
                    <div className="flex-1">
                      <h5 className="font-medium text-gray-900 mb-1">{video.title}</h5>
                      <p className="text-sm text-gray-600">
                        {video.channel_name}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-green-600 mb-1">
                        {(video.relevance_score * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-500">
                        Confidence: {(video.confidence_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}