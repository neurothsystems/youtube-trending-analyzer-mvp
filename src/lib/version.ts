import packageJson from '../../package.json';

export const FRONTEND_VERSION = packageJson.version;
export const FRONTEND_BUILD_COMMIT = process.env.NEXT_PUBLIC_BUILD_COMMIT || 'eb10e19';

export interface BackendVersionInfo {
  version: string;
  build_info?: {
    commit: string;
    features: string[];
  };
  api_version?: string;
  build_commit?: string;
  active_features?: Record<string, boolean>;
}

export interface VersionCompatibility {
  compatible: boolean;
  frontend_version: string;
  backend_version: string;
  missing_features: string[];
  version_mismatch: boolean;
}

export function checkVersionCompatibility(
  backendInfo: BackendVersionInfo
): VersionCompatibility {
  const frontendFeatures = [
    'origin_country_detection',
    'search_transparency', 
    'cache_invalidation'
  ];

  const backendFeatures = backendInfo.build_info?.features || 
                          Object.keys(backendInfo.active_features || {});

  const missingFeatures = frontendFeatures.filter(
    feature => !backendFeatures.includes(feature)
  );

  const backendVersion = backendInfo.version || backendInfo.api_version || 'unknown';
  const versionMismatch = !backendVersion.startsWith('1.1.0');

  return {
    compatible: missingFeatures.length === 0 && !versionMismatch,
    frontend_version: FRONTEND_VERSION,
    backend_version: backendVersion,
    missing_features: missingFeatures,
    version_mismatch: versionMismatch
  };
}

export function getVersionDisplayText(compatibility: VersionCompatibility): {
  text: string;
  color: 'green' | 'yellow' | 'red';
  icon: string;
} {
  if (compatibility.compatible) {
    return {
      text: `Frontend v${compatibility.frontend_version} ↔ Backend v${compatibility.backend_version}`,
      color: 'green',
      icon: '✅'
    };
  }

  if (compatibility.version_mismatch) {
    return {
      text: `Version Mismatch: Frontend v${compatibility.frontend_version} ↔ Backend v${compatibility.backend_version}`,
      color: 'red', 
      icon: '❌'
    };
  }

  return {
    text: `Missing Features: ${compatibility.missing_features.join(', ')}`,
    color: 'yellow',
    icon: '⚠️'
  };
}