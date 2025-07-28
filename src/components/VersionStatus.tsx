'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { TrendingAnalyzerAPI } from 'lib/api';
import { 
  FRONTEND_VERSION, 
  checkVersionCompatibility, 
  getVersionDisplayText,
  BackendVersionInfo 
} from 'lib/version';
import { cn } from 'lib/utils';

interface VersionStatusProps {
  className?: string;
  showDetails?: boolean;
}

export default function VersionStatus({ 
  className, 
  showDetails = false 
}: VersionStatusProps) {
  const [backendInfo, setBackendInfo] = useState<BackendVersionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBackendVersion = async () => {
      try {
        const data = await TrendingAnalyzerAPI.getBackendInfo();
        setBackendInfo(data);
      } catch (err) {
        console.error('Failed to fetch backend version:', err);
        setError('Backend unavailable');
      } finally {
        setLoading(false);
      }
    };

    fetchBackendVersion();
  }, []);

  if (loading) {
    return (
      <div className={cn("flex items-center space-x-1 text-xs text-gray-500", className)}>
        <Clock className="w-3 h-3 animate-spin" />
        <span>Checking versions...</span>
      </div>
    );
  }

  if (error || !backendInfo) {
    return (
      <div className={cn("flex items-center space-x-1 text-xs text-red-600", className)}>
        <AlertCircle className="w-3 h-3" />
        <span>Backend: {error || 'Unknown'}</span>
      </div>
    );
  }

  const compatibility = checkVersionCompatibility(backendInfo);
  const display = getVersionDisplayText(compatibility);

  const colorClasses = {
    green: 'text-green-600',
    yellow: 'text-yellow-600', 
    red: 'text-red-600'
  };

  const iconComponents = {
    green: CheckCircle,
    yellow: AlertCircle,
    red: AlertCircle
  };

  const IconComponent = iconComponents[display.color];

  return (
    <div className={cn("flex items-center space-x-1 text-xs", colorClasses[display.color], className)}>
      <IconComponent className="w-3 h-3" />
      {showDetails ? (
        <div className="flex flex-col">
          <span className="font-medium">{display.text}</span>
          {!compatibility.compatible && (
            <span className="text-gray-500">
              Features: {backendInfo.build_info?.features?.join(', ') || 'Unknown'}
            </span>
          )}
        </div>
      ) : (
        <span title={display.text}>
          Frontend v{FRONTEND_VERSION} ↔ Backend v{compatibility.backend_version}
        </span>
      )}
    </div>
  );
}