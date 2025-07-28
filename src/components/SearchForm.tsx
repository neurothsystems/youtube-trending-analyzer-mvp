'use client';

import { useState, useCallback } from 'react';
import { Search, Loader2, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { COUNTRIES, TIMEFRAMES, DEFAULT_FORM_VALUES, EXAMPLE_QUERIES, UI_CONSTANTS } from 'lib/constants';
import { validateQuery, debounce } from 'lib/utils';
import { SearchFormData, CountryCode, TimeframeOption } from 'types/api';
import CacheControls from './CacheControls';

interface SearchFormProps {
  onSearch: (data: SearchFormData) => void;
  isLoading?: boolean;
  onCacheCleared?: () => void;
}

export default function SearchForm({ onSearch, isLoading = false, onCacheCleared }: SearchFormProps) {
  const [formData, setFormData] = useState<SearchFormData>(DEFAULT_FORM_VALUES);
  const [errors, setErrors] = useState<Partial<Record<keyof SearchFormData, string>>>({});

  // Debounced validation
  const debouncedValidation = useCallback(
    debounce((query: string) => {
      const validation = validateQuery(query);
      if (!validation.valid) {
        setErrors(prev => ({ ...prev, query: validation.error }));
      } else {
        setErrors(prev => ({ ...prev, query: undefined }));
      }
    }, UI_CONSTANTS.debounceDelay),
    []
  );

  const handleInputChange = (field: keyof SearchFormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));

    // Real-time validation for query
    if (field === 'query' && typeof value === 'string') {
      debouncedValidation(value);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    const queryValidation = validateQuery(formData.query);
    if (!queryValidation.valid) {
      setErrors({ query: queryValidation.error });
      toast.error('Please fix the search query');
      return;
    }

    // Clear errors and submit with fixed limit
    setErrors({});
    onSearch({ ...formData, limit: 10 });
  };

  const handleExampleClick = (example: string) => {
    setFormData(prev => ({ ...prev, query: example }));
    setErrors(prev => ({ ...prev, query: undefined }));
  };

  const getExampleQueries = () => {
    return EXAMPLE_QUERIES[formData.country] || EXAMPLE_QUERIES.US;
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Main Search Input */}
        <div className="relative">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={formData.query}
              onChange={(e) => handleInputChange('query', e.target.value)}
              placeholder="Enter search term (e.g., AI, gaming, music)..."
              className={`w-full pl-12 pr-4 py-4 text-lg border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all ${
                errors.query ? 'border-red-500' : 'border-gray-300'
              }`}
              maxLength={UI_CONSTANTS.maxQueryLength}
              disabled={isLoading}
            />
            {isLoading && (
              <Loader2 className="absolute right-4 top-1/2 transform -translate-y-1/2 text-primary-500 w-5 h-5 animate-spin" />
            )}
          </div>
          
          {/* Error message */}
          {errors.query && (
            <p className="mt-2 text-sm text-red-600">{errors.query}</p>
          )}
          
          {/* Character count */}
          <div className="mt-2 text-right">
            <span className={`text-xs ${formData.query.length > UI_CONSTANTS.maxQueryLength * 0.9 ? 'text-red-500' : 'text-gray-400'}`}>
              {formData.query.length}/{UI_CONSTANTS.maxQueryLength}
            </span>
          </div>
        </div>

        {/* Country and Timeframe Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Country Selection */}
          <div>
            <label htmlFor="country" className="block text-sm font-medium text-gray-700 mb-2">
              Country
            </label>
            <select
              id="country"
              value={formData.country}
              onChange={(e) => handleInputChange('country', e.target.value)}
              className="select w-full"
              disabled={isLoading}
            >
              {COUNTRIES.map((country) => (
                <option key={country.code} value={country.code}>
                  <span className="country-flag">{country.flag}</span> {country.name}
                </option>
              ))}
            </select>
          </div>

          {/* Timeframe Selection */}
          <div>
            <label htmlFor="timeframe" className="block text-sm font-medium text-gray-700 mb-2">
              Timeframe
            </label>
            <select
              id="timeframe"
              value={formData.timeframe}
              onChange={(e) => handleInputChange('timeframe', e.target.value)}
              className="select w-full"
              disabled={isLoading}
            >
              {TIMEFRAMES.map((timeframe) => (
                <option key={timeframe.value} value={timeframe.value}>
                  {timeframe.label} - {timeframe.description}
                </option>
              ))}
            </select>
          </div>
        </div>


        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading || !!errors.query}
          className="w-full btn-primary h-12 text-lg font-semibold flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Analyzing Trends...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>Analyze Trending Videos</span>
            </>
          )}
        </button>

        {/* Cache Controls */}
        <div className="mt-4 flex justify-center">
          <CacheControls
            currentQuery={formData.query || undefined}
            currentCountry={formData.country}
            onCacheCleared={onCacheCleared}
          />
        </div>
      </form>

      {/* Example Queries */}
      {!isLoading && (
        <div className="mt-6">
          <p className="text-sm text-gray-600 mb-3">Popular searches for {COUNTRIES.find(c => c.code === formData.country)?.name}:</p>
          <div className="flex flex-wrap gap-2">
            {getExampleQueries().map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
                type="button"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}