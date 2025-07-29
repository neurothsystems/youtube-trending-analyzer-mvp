'use client';

import { useState, useEffect } from 'react';
import { Activity, Database, Clock, Zap, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface PerformanceData {
  period: {
    start_date: string;
    end_date: string;
    hours: number;
  };
  cache_performance: {
    status: string;
    hit_rate: number;
    hit_rate_percentage: number;
    target_hit_rate: number;
    memory_used: string;
    connected_clients: number;
  };
  system_metrics: {
    searches_per_hour: number;
    capacity_utilization: number;
    peak_capacity_estimate: number;
    avg_response_time_ms: number;
  };
  reliability: {
    uptime_percentage: number;
    error_rate: number;
    successful_requests: number;
    failed_requests: number;
  };
}

export default function SystemMetrics() {
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);
  const [hours, setHours] = useState(24);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPerformanceData();
  }, [hours]);

  const loadPerformanceData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/mvp/analytics/performance?hours=${hours}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setPerformanceData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler');
      console.error('Performance analytics error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (percentage: number, isReverse = false) => {
    if (isReverse) {
      if (percentage < 25) return 'text-green-600';
      if (percentage < 50) return 'text-yellow-600';
      return 'text-red-600';
    } else {
      if (percentage >= 80) return 'text-green-600';
      if (percentage >= 60) return 'text-yellow-600';
      return 'text-red-600';
    }
  };

  const getStatusIcon = (percentage: number, isReverse = false) => {
    const isGood = isReverse ? percentage < 25 : percentage >= 80;
    const isOk = isReverse ? percentage < 50 : percentage >= 60;
    
    if (isGood) return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (isOk) return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
    return <XCircle className="w-5 h-5 text-red-600" />;
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
            <Activity className="w-5 h-5 text-red-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-800">Fehler beim Laden der Performance-Daten</h3>
            <p className="text-red-600 mt-1">{error}</p>
            <button 
              onClick={loadPerformanceData}
              className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Erneut versuchen
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!performanceData) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
        <p className="text-gray-600">Keine Performance-Daten verfügbar</p>
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
            {[1, 6, 24, 72, 168].map((h) => (
              <button
                key={h}
                onClick={() => setHours(h)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  hours === h
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {h === 1 ? '1h' : h < 24 ? `${h}h` : `${h/24}d`}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            {getStatusIcon(performanceData.reliability.uptime_percentage)}
          </div>
          <h3 className="text-sm font-medium text-gray-600">System Uptime</h3>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {performanceData.reliability.uptime_percentage.toFixed(1)}%
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Verfügbarkeit ({hours}h)
          </p>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
            {getStatusIcon(performanceData.system_metrics.avg_response_time_ms < 2000 ? 90 : 50)}
          </div>
          <h3 className="text-sm font-medium text-gray-600">Response Time</h3>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {(performanceData.system_metrics.avg_response_time_ms / 1000).toFixed(1)}s
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Durchschnittlich
          </p>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Database className="w-6 h-6 text-purple-600" />
            </div>
            {getStatusIcon(performanceData.cache_performance.hit_rate_percentage)}
          </div>
          <h3 className="text-sm font-medium text-gray-600">Cache Hit Rate</h3>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {performanceData.cache_performance.hit_rate_percentage.toFixed(0)}%
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Target: {performanceData.cache_performance.target_hit_rate}%
          </p>
        </div>

        <div className="bg-white rounded-lg p-6 shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Zap className="w-6 h-6 text-orange-600" />
            </div>
            {getStatusIcon(performanceData.system_metrics.capacity_utilization, true)}
          </div>
          <h3 className="text-sm font-medium text-gray-600">Capacity</h3>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {performanceData.system_metrics.capacity_utilization.toFixed(0)}%
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Auslastung
          </p>
        </div>
      </div>

      {/* Cache Performance Details */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex items-center mb-6">
          <div className="p-2 bg-purple-100 rounded-lg mr-3">
            <Database className="w-6 h-6 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Cache Performance</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Hit Rate</span>
              <span className={`text-sm font-bold ${getStatusColor(performanceData.cache_performance.hit_rate_percentage)}`}>
                {performanceData.cache_performance.hit_rate_percentage.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${performanceData.cache_performance.hit_rate_percentage}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0%</span>
              <span>Target: {performanceData.cache_performance.target_hit_rate}%</span>
              <span>100%</span>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium text-gray-600">Memory Usage</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {performanceData.cache_performance.memory_used}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Redis Memory
            </p>
          </div>

          <div>
            <p className="text-sm font-medium text-gray-600">Connected Clients</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {performanceData.cache_performance.connected_clients}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Active Connections
            </p>
          </div>
        </div>
      </div>

      {/* System Load & Capacity */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex items-center mb-6">
          <div className="p-2 bg-blue-100 rounded-lg mr-3">
            <Activity className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">System Load & Kapazität</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h4 className="text-md font-medium text-gray-700 mb-4">Durchsatz</h4>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">Suchanfragen/Stunde</span>
                  <span className="text-sm font-medium text-gray-900">
                    {performanceData.system_metrics.searches_per_hour.toFixed(1)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full"
                    style={{ 
                      width: `${Math.min((performanceData.system_metrics.searches_per_hour / performanceData.system_metrics.peak_capacity_estimate) * 100, 100)}%` 
                    }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">Kapazitätsauslastung</span>
                  <span className={`text-sm font-medium ${getStatusColor(performanceData.system_metrics.capacity_utilization, true)}`}>
                    {performanceData.system_metrics.capacity_utilization.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${
                      performanceData.system_metrics.capacity_utilization > 80 
                        ? 'bg-gradient-to-r from-red-500 to-red-600'
                        : performanceData.system_metrics.capacity_utilization > 60
                        ? 'bg-gradient-to-r from-yellow-500 to-yellow-600'
                        : 'bg-gradient-to-r from-green-500 to-green-600'
                    }`}
                    style={{ width: `${Math.min(performanceData.system_metrics.capacity_utilization, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-md font-medium text-gray-700 mb-4">Zuverlässigkeit</h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Erfolgreiche Anfragen</span>
                <span className="text-sm font-medium text-green-600">
                  {performanceData.reliability.successful_requests.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Fehlgeschlagene Anfragen</span>
                <span className="text-sm font-medium text-red-600">
                  {performanceData.reliability.failed_requests.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Error Rate</span>
                <span className={`text-sm font-medium ${getStatusColor(performanceData.reliability.error_rate, true)}`}>
                  {performanceData.reliability.error_rate.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Ø Response Time</span>
                <span className="text-sm font-medium text-blue-600">
                  {(performanceData.system_metrics.avg_response_time_ms / 1000).toFixed(2)}s
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex items-center mb-6">
          <div className="p-2 bg-green-100 rounded-lg mr-3">
            <CheckCircle className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'API Gateway', status: 'online', color: 'green' },
            { label: 'Database', status: 'online', color: 'green' },
            { label: 'Redis Cache', status: performanceData.cache_performance.status === 'connected' ? 'online' : 'offline', color: performanceData.cache_performance.status === 'connected' ? 'green' : 'red' },
            { label: 'LLM Service', status: 'online', color: 'green' }
          ].map((service) => (
            <div key={service.label} className="flex items-center justify-between p-3 border rounded-lg">
              <span className="text-sm font-medium text-gray-700">{service.label}</span>
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${
                  service.color === 'green' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className={`text-xs font-medium ${
                  service.color === 'green' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {service.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}