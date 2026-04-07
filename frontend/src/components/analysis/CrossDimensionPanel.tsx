import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { CrossDimensionResponse, CrossDimensionResult, CrossDimensionRecommendation } from '../../types';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface CrossDimensionPanelProps {
  crossDimension: CrossDimensionResponse | null;
  isLoading?: boolean;
}

/**
 * 交叉维度结果面板
 * 
 * 展示交叉维度校验的推荐结果和状态。
 */
export const CrossDimensionPanel: React.FC<CrossDimensionPanelProps> = ({
  crossDimension,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="p-3 bg-purple-50 dark:bg-purple-900/10 rounded-lg border border-purple-100 dark:border-purple-800">
        <div className="flex items-center gap-2 text-sm text-purple-700 dark:text-purple-300">
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span>交叉维度计算中...</span>
        </div>
      </div>
    );
  }

  if (!crossDimension || (!crossDimension.recommendations.length && !crossDimension.results.length)) {
    return null;
  }

  const hasSignificant = crossDimension.results.some((r) => r.is_significant);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          交叉维度校验
        </h4>
        {!crossDimension.completed && (
          <span className="text-[10px] px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full animate-pulse" />
            计算中
          </span>
        )}
        {crossDimension.completed && hasSignificant && (
          <span className="text-[10px] px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full">
            发现显著交叉影响
          </span>
        )}
        {crossDimension.completed && !hasSignificant && (
          <span className="text-[10px] px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full">
            无显著交叉影响
          </span>
        )}
      </div>

      {/* 推荐列表 */}
      {crossDimension.recommendations.length > 0 && (
        <div className="space-y-2">
          {crossDimension.recommendations.map((rec, index) => (
            <RecommendationCard key={index} recommendation={rec} />
          ))}
        </div>
      )}

      {/* 详细结果 */}
      {crossDimension.results.length > 0 && (
        <div className="space-y-2">
          {crossDimension.results.map((result, index) => (
            <ResultCard key={index} result={result} />
          ))}
        </div>
      )}
    </div>
  );
};

const RecommendationCard: React.FC<{ recommendation: CrossDimensionRecommendation }> = ({ recommendation }) => {
  const [a, b] = recommendation.dimension_pair;
  return (
    <div className="p-3 bg-purple-50 dark:bg-purple-900/10 rounded-lg border border-purple-100 dark:border-purple-800">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
          {a} × {b}
        </span>
        <span className="text-xs text-purple-600 dark:text-purple-400">
          熵减 {(recommendation.entropy_reduction * 100).toFixed(1)}%
        </span>
      </div>
      <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
        {recommendation.reason}
      </p>
    </div>
  );
};

const ResultCard: React.FC<{ result: CrossDimensionResult }> = ({ result }) => {
  const [a, b] = result.dimension_pair;
  return (
    <div
      className={cn(
        'p-3 rounded-lg border',
        result.is_significant
          ? 'bg-purple-50 dark:bg-purple-900/10 border-purple-200 dark:border-purple-800'
          : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
      )}
    >
      <div className="flex items-center justify-between">
        <span
          className={cn(
            'text-sm font-medium',
            result.is_significant
              ? 'text-purple-700 dark:text-purple-300'
              : 'text-gray-700 dark:text-gray-300'
          )}
        >
          {a} × {b}
          {result.is_significant && (
            <span className="ml-1 text-purple-500">★</span>
          )}
        </span>
        <span
          className={cn(
            'text-xs',
            result.is_significant
              ? 'text-purple-600 dark:text-purple-400'
              : 'text-gray-500 dark:text-gray-400'
          )}
        >
          熵减 {(result.entropy_reduction * 100).toFixed(1)}%
        </span>
      </div>
      {result.top_combination && (
        <div className="mt-2 flex items-center gap-2 text-xs">
          <span className="text-gray-500">最佳组合:</span>
          <span
            className={cn(
              'px-2 py-0.5 rounded font-medium',
              result.is_significant
                ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            )}
          >
            {result.top_combination}
          </span>
          <span className="text-gray-400">({(result.top_combination_share * 100).toFixed(1)}%)</span>
        </div>
      )}
    </div>
  );
};
