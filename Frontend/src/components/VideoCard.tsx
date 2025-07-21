'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ExternalLink, Eye, ThumbsUp, MessageCircle, Clock, Award } from 'lucide-react';
import { TrendingVideo } from '@/types/api';
import { 
  formatViews, 
  formatRelativeTime, 
  getTrendingScoreColor, 
  getTrendingScoreLabel,
  getRelevanceScoreColor,
  getRelevanceScoreLabel,
  truncateText,
  calculatePercentage,
  getYouTubeThumbnail
} from '@/lib/utils';
import { cn } from '@/lib/utils';

interface VideoCardProps {
  video: TrendingVideo;
  index: number;
}

export default function VideoCard({ video, index }: VideoCardProps) {
  const trendingColor = getTrendingScoreColor(video.trending_score);
  const trendingLabel = getTrendingScoreLabel(video.trending_score);
  const relevanceColor = getRelevanceScoreColor(video.country_relevance_score);
  const relevanceLabel = getRelevanceScoreLabel(video.country_relevance_score);

  // Calculate score percentages for visual bars
  const trendingPercentage = calculatePercentage(video.trending_score, 10000);
  const relevancePercentage = video.country_relevance_score * 100;

  return (
    <div 
      className="card p-0 hover:shadow-lg transition-all duration-300 overflow-hidden animate-fade-in-up"
      style={{ animationDelay: `${index * 150}ms` }}
    >
      {/* Rank Badge */}
      <div className="absolute top-4 left-4 z-10">
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm shadow-lg",
          video.rank <= 3 ? "bg-gradient-to-r from-yellow-400 to-yellow-600" : "bg-gradient-to-r from-gray-500 to-gray-600"
        )}>
          {video.rank}
        </div>
      </div>

      {/* Trending Feed Badge */}
      {video.is_in_trending_feed && (
        <div className="absolute top-4 right-4 z-10">
          <div className="bg-red-500 text-white px-2 py-1 rounded-full text-xs font-semibold flex items-center space-x-1">
            <Award className="w-3 h-3" />
            <span>Trending</span>
          </div>
        </div>
      )}

      {/* Thumbnail */}
      <div className="relative">
        <Link href={video.url} target="_blank" rel="noopener noreferrer">
          <div className="relative aspect-video bg-gray-200 overflow-hidden">
            <Image
              src={video.thumbnail || getYouTubeThumbnail(video.video_id)}
              alt={video.title}
              fill
              className="object-cover hover:scale-105 transition-transform duration-300"
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src = getYouTubeThumbnail(video.video_id, 'medium');
              }}
            />
            
            {/* Play overlay */}
            <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-10 transition-all duration-300 flex items-center justify-center">
              <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-300">
                <div className="w-0 h-0 border-l-[12px] border-l-white border-y-[8px] border-y-transparent ml-1"></div>
              </div>
            </div>
          </div>
        </Link>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Title and Channel */}
        <div>
          <Link href={video.url} target="_blank" rel="noopener noreferrer">
            <h3 className="font-semibold text-gray-900 line-clamp-2 hover:text-primary-600 transition-colors">
              {video.title}
            </h3>
          </Link>
          <p className="text-sm text-gray-600 mt-1">
            {video.channel} {video.channel_country && `• ${video.channel_country}`}
          </p>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <Eye className="w-4 h-4" />
              <span>{formatViews(video.views)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <ThumbsUp className="w-4 h-4" />
              <span>{formatViews(video.likes)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <MessageCircle className="w-4 h-4" />
              <span>{formatViews(video.comments)}</span>
            </div>
          </div>
          
          {video.upload_date && (
            <div className="flex items-center space-x-1">
              <Clock className="w-4 h-4" />
              <span>{formatRelativeTime(video.upload_date)}</span>
            </div>
          )}
        </div>

        {/* Score Bars */}
        <div className="space-y-3">
          {/* Trending Score */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-700">Trending Score</span>
              <span className="text-sm font-semibold" style={{ color: trendingColor }}>
                {video.trending_score.toLocaleString()} ({trendingLabel})
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all duration-500"
                style={{
                  width: `${trendingPercentage}%`,
                  backgroundColor: trendingColor
                }}
              />
            </div>
          </div>

          {/* Country Relevance */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium text-gray-700">Country Relevance</span>
              <span className="text-sm font-semibold" style={{ color: relevanceColor }}>
                {Math.round(video.country_relevance_score * 100)}% ({relevanceLabel})
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all duration-500"
                style={{
                  width: `${relevancePercentage}%`,
                  backgroundColor: relevanceColor
                }}
              />
            </div>
          </div>
        </div>

        {/* LLM Reasoning */}
        {video.reasoning && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800 font-medium mb-1">AI Analysis:</p>
            <p className="text-sm text-blue-700">
              {truncateText(video.reasoning, 120)}
            </p>
          </div>
        )}

        {/* Engagement Rate */}
        <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
          <span>Engagement: {video.engagement_rate.toFixed(2)}%</span>
          <span>Age: {video.age_hours.toFixed(1)}h</span>
          <Link 
            href={video.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center space-x-1 text-primary-600 hover:text-primary-700 transition-colors"
          >
            <span>Watch</span>
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      </div>
    </div>
  );
}