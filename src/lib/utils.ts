import { clsx, type ClassValue } from 'clsx';
import { format, formatDistanceToNow, isValid, parseISO } from 'date-fns';
import { 
  TRENDING_SCORE_THRESHOLDS, 
  RELEVANCE_SCORE_THRESHOLDS, 
  COLORS,
  COUNTRIES,
  TIMEFRAMES 
} from './constants';
import { CountryCode, TimeframeOption, Country, TimeframeInfo } from 'types/api';

/**
 * Utility function to combine class names
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/**
 * Format large numbers with K/M/B suffixes
 */
export function formatNumber(num: number): string {
  if (num < 1000) return num.toString();
  if (num < 1000000) return (num / 1000).toFixed(1).replace('.0', '') + 'K';
  if (num < 1000000000) return (num / 1000000).toFixed(1).replace('.0', '') + 'M';
  return (num / 1000000000).toFixed(1).replace('.0', '') + 'B';
}

/**
 * Format view count with proper suffix
 */
export function formatViews(views: number): string {
  const formatted = formatNumber(views);
  return `${formatted} view${views !== 1 ? 's' : ''}`;
}

/**
 * Format duration in seconds to human readable format
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Format date string to relative time
 */
export function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return 'Unknown';
  
  try {
    const date = parseISO(dateString);
    if (!isValid(date)) return 'Invalid date';
    
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return 'Invalid date';
  }
}

/**
 * Format absolute date
 */
export function formatDate(dateString: string | null, formatString: string = 'PPp'): string {
  if (!dateString) return 'Unknown';
  
  try {
    const date = parseISO(dateString);
    if (!isValid(date)) return 'Invalid date';
    
    return format(date, formatString);
  } catch {
    return 'Invalid date';
  }
}

/**
 * Get trending score color based on thresholds
 */
export function getTrendingScoreColor(score: number): string {
  if (score >= TRENDING_SCORE_THRESHOLDS.EXCELLENT) return COLORS.trending.excellent;
  if (score >= TRENDING_SCORE_THRESHOLDS.GOOD) return COLORS.trending.good;
  if (score >= TRENDING_SCORE_THRESHOLDS.MODERATE) return COLORS.trending.moderate;
  if (score >= TRENDING_SCORE_THRESHOLDS.LOW) return COLORS.trending.low;
  return COLORS.trending.poor;
}

/**
 * Get relevance score color based on thresholds
 */
export function getRelevanceScoreColor(score: number): string {
  if (score >= RELEVANCE_SCORE_THRESHOLDS.VERY_HIGH) return COLORS.relevance.veryHigh;
  if (score >= RELEVANCE_SCORE_THRESHOLDS.HIGH) return COLORS.relevance.high;
  if (score >= RELEVANCE_SCORE_THRESHOLDS.MODERATE) return COLORS.relevance.moderate;
  if (score >= RELEVANCE_SCORE_THRESHOLDS.LOW) return COLORS.relevance.low;
  return COLORS.relevance.veryLow;
}

/**
 * Get trending score label
 */
export function getTrendingScoreLabel(score: number): string {
  if (score >= TRENDING_SCORE_THRESHOLDS.EXCELLENT) return 'Excellent';
  if (score >= TRENDING_SCORE_THRESHOLDS.GOOD) return 'Good';
  if (score >= TRENDING_SCORE_THRESHOLDS.MODERATE) return 'Moderate';
  if (score >= TRENDING_SCORE_THRESHOLDS.LOW) return 'Low';
  return 'Poor';
}

/**
 * Get relevance score label
 */
export function getRelevanceScoreLabel(score: number): string {
  if (score >= RELEVANCE_SCORE_THRESHOLDS.VERY_HIGH) return 'Very High';
  if (score >= RELEVANCE_SCORE_THRESHOLDS.HIGH) return 'High';
  if (score >= RELEVANCE_SCORE_THRESHOLDS.MODERATE) return 'Moderate';
  if (score >= RELEVANCE_SCORE_THRESHOLDS.LOW) return 'Low';
  return 'Very Low';
}

/**
 * Calculate percentage for progress bars
 */
export function calculatePercentage(value: number, max: number): number {
  return Math.min(Math.max((value / max) * 100, 0), 100);
}

/**
 * Get country information by code
 */
export function getCountryInfo(code: CountryCode): Country {
  const country = COUNTRIES.find(c => c.code === code);
  if (!country) {
    throw new Error(`Unsupported country code: ${code}`);
  }
  return country;
}

/**
 * Get timeframe information by value
 */
export function getTimeframeInfo(value: TimeframeOption): TimeframeInfo {
  const timeframe = TIMEFRAMES.find(t => t.value === value);
  if (!timeframe) {
    throw new Error(`Unsupported timeframe: ${value}`);
  }
  return timeframe;
}

/**
 * Validate search query
 */
export function validateQuery(query: string): { valid: boolean; error?: string } {
  const trimmed = query.trim();
  
  if (!trimmed) {
    return { valid: false, error: 'Search query is required' };
  }
  
  if (trimmed.length < 2) {
    return { valid: false, error: 'Search query must be at least 2 characters long' };
  }
  
  if (trimmed.length > 100) {
    return { valid: false, error: 'Search query must be less than 100 characters' };
  }
  
  return { valid: true };
}

/**
 * Generate YouTube thumbnail URL with different sizes
 */
export function getYouTubeThumbnail(videoId: string, quality: 'default' | 'medium' | 'high' | 'standard' | 'maxres' = 'high'): string {
  return `https://img.youtube.com/vi/${videoId}/${quality === 'high' ? 'hqdefault' : quality === 'medium' ? 'mqdefault' : quality === 'standard' ? 'sddefault' : quality === 'maxres' ? 'maxresdefault' : 'default'}.jpg`;
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
}

/**
 * Generate random color for charts/visualizations
 */
export function generateColor(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    const char = seed.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 70%, 50%)`;
}

/**
 * Debounce function for search input
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

/**
 * Format percentage with proper rounding
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format currency (EUR)
 */
export function formatCurrency(amount: number, currency: string = 'EUR'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
}

/**
 * Calculate engagement rate
 */
export function calculateEngagementRate(likes: number, comments: number, views: number): number {
  if (views === 0) return 0;
  return ((likes + comments) / views) * 100;
}

/**
 * Get status color for health checks
 */
export function getStatusColor(status: 'healthy' | 'degraded' | 'unhealthy' | 'warning' | 'critical' | string): string {
  switch (status.toLowerCase()) {
    case 'healthy':
    case 'ok':
    case 'good':
      return COLORS.status.healthy;
    case 'degraded':
    case 'warning':
    case 'caution':
      return COLORS.status.warning;
    case 'unhealthy':
    case 'critical':
    case 'error':
      return COLORS.status.critical;
    default:
      return COLORS.status.unknown;
  }
}

/**
 * Sleep utility for testing/delays
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      const successful = document.execCommand('copy');
      document.body.removeChild(textArea);
      return successful;
    } catch {
      return false;
    }
  }
}