'use client';

import { useState, useEffect } from 'react';
import { BarChart3, DollarSign, Zap, Activity, TrendingUp, Clock, Database, Globe } from 'lucide-react';
import Header from 'components/Header';
import CostAnalytics from 'components/CostAnalytics';
import SystemMetrics from 'components/SystemMetrics';
import ContentInsights from 'components/ContentInsights';
import RealTimeMonitor from 'components/RealTimeMonitor';

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState('costs');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initial load delay
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  const tabs = [
    { id: 'costs', label: 'LLM & Kosten', icon: DollarSign, color: 'text-green-600' },
    { id: 'performance', label: 'System-Performance', icon: Zap, color: 'text-blue-600' },
    { id: 'content', label: 'Content-Analyse', icon: BarChart3, color: 'text-purple-600' },
    { id: 'realtime', label: 'Live-Monitoring', icon: Activity, color: 'text-red-600' }
  ];

  const renderTabContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <span className="ml-3 text-gray-600">Analytics laden...</span>
        </div>
      );
    }

    switch (activeTab) {
      case 'costs':
        return <CostAnalytics />;
      case 'performance':
        return <SystemMetrics />;
      case 'content':
        return <ContentInsights />;
      case 'realtime':
        return <RealTimeMonitor />;
      default:
        return <CostAnalytics />;
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
              <p className="text-gray-600">Umfassende Metriken und Insights für das YouTube Trending Analyzer System</p>
            </div>
          </div>
          
          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-lg p-4 shadow-sm border">
              <div className="flex items-center">
                <DollarSign className="w-5 h-5 text-green-600 mr-2" />
                <span className="text-sm font-medium text-gray-600">Heutige Kosten</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-1">$0.0024</p>
              <p className="text-xs text-green-600">↓ 67% günstiger</p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm border">
              <div className="flex items-center">
                <Activity className="w-5 h-5 text-blue-600 mr-2" />
                <span className="text-sm font-medium text-gray-600">Token/Stunde</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-1">847</p>
              <p className="text-xs text-blue-600">↑ Optimiert</p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm border">
              <div className="flex items-center">
                <Clock className="w-5 h-5 text-purple-600 mr-2" />
                <span className="text-sm font-medium text-gray-600">Cache Hit Rate</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-1">73%</p>
              <p className="text-xs text-purple-600">↑ Sehr gut</p>
            </div>
            
            <div className="bg-white rounded-lg p-4 shadow-sm border">
              <div className="flex items-center">
                <Database className="w-5 h-5 text-orange-600 mr-2" />
                <span className="text-sm font-medium text-gray-600">Videos analysiert</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-1">1,247</p>
              <p className="text-xs text-orange-600">Letzte 7 Tage</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-sm border mb-6">
          <div className="flex border-b border-gray-200">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-6 py-4 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? `${tab.color} bg-gray-50 border-b-2 border-current`
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="animate-fade-in">
          {renderTabContent()}
        </div>
      </main>
    </div>
  );
}