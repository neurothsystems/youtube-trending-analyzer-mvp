'use client';

import { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, Zap, Target, PieChart, BarChart3 } from 'lucide-react';
import { TrendingAnalyzerAPI } from 'lib/api';

interface CostData {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  totals: {
    cost_usd: number;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    requests: number;
    avg_processing_time_ms: number;
    cost_per_request: number;
  };
  daily_breakdown: Array<{
    date: string;
    cost_usd: number;
    input_tokens: number;
    output_tokens: number;
    requests: number;
  }>;
  country_breakdown: Array<{
    country: string;
    cost_usd: number;
    input_tokens: number;
    output_tokens: number;
    requests: number;
  }>;
  cache_efficiency: Record<string, {
    requests: number;
    cost_usd: number;
  }>;
  model_info: {
    current_model: string;
    input_cost_per_1m_tokens: number;
    output_cost_per_1m_tokens: number;
    currency: string;
  };
}

export default function CostAnalytics() {
  const [costData, setCostData] = useState<CostData | null>(null);
  const [days, setDays] = useState(7);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCostData();
  }, [days]);

  const loadCostData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/mvp/analytics/llm-costs?days=${days}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setCostData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler');
      console.error('Cost analytics error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number, currency = 'USD') => {
    if (currency === 'USD') {
      return `$${amount.toFixed(6)}`;
    }
    return `€${amount.toFixed(6)}`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString('de-DE');
  };

  const calculateCacheHitRate = () => {
    if (!costData?.cache_efficiency) return '0%';
    
    const trueHits = costData.cache_efficiency.true?.requests || 0;
    const falseHits = costData.cache_efficiency.false?.requests || 0;
    const total = trueHits + falseHits;
    
    if (total === 0) return '0%';
    return `${Math.round((trueHits / total) * 100)}%`;
  };

  const calculateSavings = () => {
    if (!costData) return '0%';
    
    // Compare with old Gemini 1.5 Flash pricing ($0.20/$0.20)
    const oldInputCost = costData.totals.input_tokens * (0.20 / 1_000_000);
    const oldOutputCost = costData.totals.output_tokens * (0.20 / 1_000_000);
    const oldTotalCost = oldInputCost + oldOutputCost;
    
    if (oldTotalCost === 0) return '0%';
    
    const savings = ((oldTotalCost - costData.totals.cost_usd) / oldTotalCost) * 100;
    return `${Math.round(savings)}%`;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[...Array(4)].map((_, i) => (
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
            <DollarSign className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-800">Fehler beim Laden der Kostendaten</h3>
            <p className="text-red-600 mt-1">{error}</p>
            <button 
              onClick={loadCostData}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Erneut versuchen
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!costData) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <DollarSign className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600">Keine Kostendaten verfügbar</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Time Period Selector */}
      <div className="bg-white rounded-lg p-4 shadow-sm border">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Zeitraum wählen</h2>
          <div className="flex space-x-2">
            {[1, 7, 14, 30].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  days === d
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {d === 1 ? '24h' : `${d}d`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Cost Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign className="w-6 h-6 text-green-600" />
            </div>
            <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded">
              -{calculateSavings()} vs. Alt
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600">Gesamtkosten ({days}d)</h3>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {formatCurrency(costData.totals.cost_usd)}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {formatNumber(costData.totals.requests)} Anfragen
          </p>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Zap className="w-6 h-6 text-blue-600" />
            </div>
            <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
              Tokens
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600">Token-Verbrauch</h3>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {formatNumber(costData.totals.total_tokens)}
          </p>
          <div className="flex justify-between text-sm text-gray-500 mt-1">
            <span>↗ {formatNumber(costData.totals.input_tokens)} in</span>
            <span>↘ {formatNumber(costData.totals.output_tokens)} out</span>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Target className="w-6 h-6 text-purple-600" />
            </div>
            <span className="text-sm font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded">
              Cache
            </span>
          </div>
          <h3 className="text-sm font-medium text-gray-600">Cache Hit Rate</h3>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {calculateCacheHitRate()}
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Ersparnis durch Caching
          </p>
        </div>
      </div>

      {/* Model Information */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-indigo-100 rounded-lg mr-3">
            <BarChart3 className="w-6 h-6 text-indigo-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Modell-Information</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm font-medium text-gray-600">Aktuelles Modell</p>
            <p className="text-lg font-bold text-gray-900 mt-1">{costData.model_info.current_model}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Input-Kosten</p>
            <p className="text-lg font-bold text-green-600 mt-1">
              ${costData.model_info.input_cost_per_1m_tokens}/1M
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Output-Kosten</p>
            <p className="text-lg font-bold text-orange-600 mt-1">
              ${costData.model_info.output_cost_per_1m_tokens}/1M
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-600">Ø Kosten/Anfrage</p>
            <p className="text-lg font-bold text-gray-900 mt-1">
              {formatCurrency(costData.totals.cost_per_request)}
            </p>
          </div>
        </div>
      </div>

      {/* Daily Breakdown */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex items-center mb-6">
          <div className="p-2 bg-blue-100 rounded-lg mr-3">
            <TrendingUp className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Tägliche Kostenentwicklung</h3>
        </div>
        
        <div className="space-y-3">
          {costData.daily_breakdown.map((day, index) => {
            const maxCost = Math.max(...costData.daily_breakdown.map(d => d.cost_usd));
            const barWidth = maxCost > 0 ? (day.cost_usd / maxCost) * 100 : 0;
            
            return (
              <div key={day.date} className="flex items-center">
                <div className="w-20 text-sm text-gray-600">
                  {new Date(day.date).toLocaleDateString('de-DE', { 
                    month: 'short', 
                    day: 'numeric' 
                  })}
                </div>
                <div className="flex-1 ml-4">
                  <div className="bg-gray-100 rounded-full h-6 relative">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-blue-600 h-6 rounded-full flex items-center justify-end pr-2"
                      style={{ width: `${Math.max(barWidth, 5)}%` }}
                    >
                      <span className="text-xs text-white font-medium">
                        {formatCurrency(day.cost_usd)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="w-20 text-right text-sm text-gray-600">
                  {day.requests} Req
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Country Breakdown */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex items-center mb-6">
          <div className="p-2 bg-purple-100 rounded-lg mr-3">
            <PieChart className="w-6 h-6 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Kosten nach Ländern</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {costData.country_breakdown.map((country) => (
            <div key={country.country} className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">
                    {country.country === 'DE' ? '🇩🇪' : 
                     country.country === 'US' ? '🇺🇸' :
                     country.country === 'FR' ? '🇫🇷' :
                     country.country === 'JP' ? '🇯🇵' : '🌍'}
                  </span>
                  <span className="font-medium text-gray-900">{country.country}</span>
                </div>
                <span className="text-lg font-bold text-gray-900">
                  {formatCurrency(country.cost_usd)}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                {formatNumber(country.requests)} Anfragen • {formatNumber(country.input_tokens + country.output_tokens)} Tokens
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}