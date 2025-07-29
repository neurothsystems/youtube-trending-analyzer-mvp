'use client';

import { useState, useEffect } from 'react';
import { Activity, Wifi, AlertCircle, CheckCircle, Clock, Database, Zap } from 'lucide-react';

interface SystemStatus {
  timestamp: string;
  services: {
    api: { status: 'online' | 'offline' | 'degraded', response_time: number };
    database: { status: 'online' | 'offline' | 'degraded', connections: number };
    cache: { status: 'online' | 'offline' | 'degraded', hit_rate: number };
    llm: { status: 'online' | 'offline' | 'degraded', cost_today: number };
  };
  current_load: {
    searches_per_minute: number;
    active_requests: number;
    queue_depth: number;
  };
  alerts: Array<{
    type: 'info' | 'warning' | 'error';
    message: string;
    timestamp: string;
  }>;
}

export default function RealTimeMonitor() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Simulate real-time updates
  useEffect(() => {
    const updateStatus = () => {
      // Simulate live system data
      const mockStatus: SystemStatus = {
        timestamp: new Date().toISOString(),
        services: {
          api: { 
            status: Math.random() > 0.95 ? 'degraded' : 'online', 
            response_time: 1200 + Math.random() * 800 
          },
          database: { 
            status: 'online', 
            connections: Math.floor(3 + Math.random() * 7) 
          },
          cache: { 
            status: 'online', 
            hit_rate: 0.7 + Math.random() * 0.25 
          },
          llm: { 
            status: 'online', 
            cost_today: 0.0024 + Math.random() * 0.0010 
          }
        },
        current_load: {
          searches_per_minute: Math.floor(Math.random() * 15),
          active_requests: Math.floor(Math.random() * 5),
          queue_depth: Math.floor(Math.random() * 3)
        },
        alerts: [
          {
            type: 'info',
            message: 'System läuft stabil - alle Services operativ',
            timestamp: new Date(Date.now() - Math.random() * 30000).toISOString()
          },
          {
            type: 'info', 
            message: 'Cache Hit Rate über Zielwert (73%)',
            timestamp: new Date(Date.now() - Math.random() * 60000).toISOString()
          }
        ]
      };

      setSystemStatus(mockStatus);
      setLastUpdate(new Date());
      setIsConnected(true);
    };

    // Initial load
    updateStatus();
    
    // Update every 5 seconds
    const interval = setInterval(updateStatus, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'degraded':
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'offline':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'offline':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
    }
  };

  if (!systemStatus) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg p-6 shadow-sm border animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="bg-white rounded-lg p-4 shadow-sm border">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={`p-2 rounded-lg mr-3 ${isConnected ? 'bg-green-100' : 'bg-red-100'}`}>
              <Wifi className={`w-5 h-5 ${isConnected ? 'text-green-600' : 'text-red-600'}`} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Live System Monitor</h2>
              <p className="text-sm text-gray-600">
                {isConnected ? 'Verbunden' : 'Getrennt'} • 
                Letzte Aktualisierung: {lastUpdate?.toLocaleTimeString('de-DE') || 'Nie'}
              </p>
            </div>
          </div>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className="text-sm font-medium text-gray-600">
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </div>

      {/* Service Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className={`rounded-lg p-6 shadow-sm border ${getStatusColor(systemStatus.services.api.status)}`}>
          <div className="flex items-center justify-between mb-4">
            <Activity className="w-6 h-6" />
            {getStatusIcon(systemStatus.services.api.status)}
          </div>
          <h3 className="font-medium mb-1">API Gateway</h3>
          <p className="text-2xl font-bold mb-1">
            {systemStatus.services.api.response_time.toFixed(0)}ms
          </p>
          <p className="text-sm opacity-75">Response Time</p>
        </div>

        <div className={`rounded-lg p-6 shadow-sm border ${getStatusColor(systemStatus.services.database.status)}`}>
          <div className="flex items-center justify-between mb-4">
            <Database className="w-6 h-6" />
            {getStatusIcon(systemStatus.services.database.status)}
          </div>
          <h3 className="font-medium mb-1">Database</h3>
          <p className="text-2xl font-bold mb-1">
            {systemStatus.services.database.connections}
          </p>
          <p className="text-sm opacity-75">Active Connections</p>
        </div>

        <div className={`rounded-lg p-6 shadow-sm border ${getStatusColor(systemStatus.services.cache.status)}`}>
          <div className="flex items-center justify-between mb-4">
            <Zap className="w-6 h-6" />
            {getStatusIcon(systemStatus.services.cache.status)}
          </div>
          <h3 className="font-medium mb-1">Redis Cache</h3>
          <p className="text-2xl font-bold mb-1">
            {(systemStatus.services.cache.hit_rate * 100).toFixed(0)}%
          </p>
          <p className="text-sm opacity-75">Hit Rate</p>
        </div>

        <div className={`rounded-lg p-6 shadow-sm border ${getStatusColor(systemStatus.services.llm.status)}`}>
          <div className="flex items-center justify-between mb-4">
            <Zap className="w-6 h-6" />
            {getStatusIcon(systemStatus.services.llm.status)}
          </div>
          <h3 className="font-medium mb-1">LLM Service</h3>
          <p className="text-2xl font-bold mb-1">
            ${systemStatus.services.llm.cost_today.toFixed(4)}
          </p>
          <p className="text-sm opacity-75">Today's Cost</p>
        </div>
      </div>

      {/* Current Load */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex items-center mb-6">
          <div className="p-2 bg-blue-100 rounded-lg mr-3">
            <Activity className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Aktuelle Systemlast</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Suchanfragen/Min</span>
              <span className="text-lg font-bold text-blue-600">
                {systemStatus.current_load.searches_per_minute}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min((systemStatus.current_load.searches_per_minute / 20) * 100, 100)}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Aktive Anfragen</span>
              <span className="text-lg font-bold text-green-600">
                {systemStatus.current_load.active_requests}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min((systemStatus.current_load.active_requests / 10) * 100, 100)}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Warteschlange</span>
              <span className="text-lg font-bold text-purple-600">
                {systemStatus.current_load.queue_depth}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-purple-500 to-purple-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min((systemStatus.current_load.queue_depth / 5) * 100, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Live Activity Feed */}
      <div className="bg-white rounded-lg p-6 shadow-sm border">
        <div className="flex items-center mb-6">
          <div className="p-2 bg-green-100 rounded-lg mr-3">
            <Clock className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">Live Activity Feed</h3>
        </div>
        
        <div className="space-y-3">
          {systemStatus.alerts.map((alert, index) => (
            <div key={index} className="flex items-start p-3 bg-gray-50 rounded-lg">
              <div className="mr-3 mt-0.5">
                {getAlertIcon(alert.type)}
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900">{alert.message}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(alert.timestamp).toLocaleTimeString('de-DE')}
                </p>
              </div>
            </div>
          ))}
          
          {/* Simulated live entries */}
          <div className="flex items-start p-3 bg-blue-50 rounded-lg border-l-4 border-blue-500">
            <div className="mr-3 mt-0.5">
              <CheckCircle className="w-4 h-4 text-blue-500" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-900">
                Neue Suchanfrage verarbeitet: "{['gaming', 'musik', 'tech', 'news'][Math.floor(Math.random() * 4)]}" in DE
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date().toLocaleTimeString('de-DE')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}