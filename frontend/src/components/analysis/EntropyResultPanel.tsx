import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { SingleDimensionResult } from '../../services/api';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface EntropyResultPanelProps {
  results: SingleDimensionResult[];
  selectedDimension: string | null;
  selectedChild: string | null;
  isLoading?: boolean;
  onDrillDown?: (dimension: string, child: string) => void;
  crossDimensionSignificant?: boolean;
}

/**
 * 熵减结果面板
 * 
 * 展示熵减计算结果的可视化面板
 */
export const EntropyResultPanel: React.FC<EntropyResultPanelProps> = ({
  results,
  selectedDimension,
  selectedChild,
  isLoading,
  onDrillDown,
  crossDimensionSignificant,
}) => {
  if (isLoading) {
    return <LoadingState />;
  }

  if (!results || results.length === 0) {
    return <EmptyState />;
  }

  // 按熵减值排序
  const sortedResults = [...results].sort(
    (a, b) => b.entropy_reduction_normalized - a.entropy_reduction_normalized
  );

  const bestResult = sortedResults[0];

  return (
    <div className="space-y-4">
      {/* 摘要卡片 */}
      <SummaryCard 
        selectedDimension={selectedDimension} 
        selectedChild={selectedChild}
        bestResult={bestResult}
        crossDimensionSignificant={crossDimensionSignificant}
      />

      {/* 维度对比图表 */}
      <DimensionChart results={sortedResults} />

      {/* 各维度详细分析 */}
      <DimensionDetails 
        results={sortedResults} 
        onDrillDown={onDrillDown}
      />
    </div>
  );
};

// 加载状态
const LoadingState: React.FC = () => (
  <div className="p-6 text-center">
    <div className="inline-flex items-center gap-2 text-gray-500">
      <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
      </svg>
      <span className="text-sm">正在计算熵减...</span>
    </div>
  </div>
);

// 空状态
const EmptyState: React.FC = () => (
  <div className="p-6 text-center text-gray-500">
    <svg className="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
    <p className="text-sm">暂无分析结果</p>
    <p className="text-xs text-gray-400 mt-1">点击指标树节点开始分析</p>
  </div>
);

// 摘要卡片
interface SummaryCardProps {
  selectedDimension: string | null;
  selectedChild: string | null;
  bestResult: SingleDimensionResult;
  crossDimensionSignificant?: boolean;
}

const SummaryCard: React.FC<SummaryCardProps> = ({
  selectedDimension,
  selectedChild,
  bestResult,
  crossDimensionSignificant,
}) => {
  if (!selectedDimension) {
    return (
      <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
        <p className="text-sm text-gray-500">未找到关键维度</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-4 border border-blue-100 dark:border-blue-800">
      <h4 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
        分析结论
      </h4>
      <p className="text-sm text-blue-800 dark:text-blue-200">
        维度「<span className="font-semibold">{selectedDimension}</span>」的熵减为 
        <span className="font-semibold">{(bestResult.entropy_reduction_normalized * 100).toFixed(1)}%</span>，
        建议优先从此维度下钻。
      </p>
      {selectedChild && (
        <div className="mt-2 flex items-center gap-2">
          <span className="text-xs text-blue-600 dark:text-blue-400">推荐节点:</span>
          <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 text-xs rounded-full font-medium">
            {selectedChild}
          </span>
          <span className="text-xs text-blue-600 dark:text-blue-400">
            (占比 {bestResult.top_child_share.toFixed(1)}%)
          </span>
        </div>
      )}
      {crossDimensionSignificant && (
        <div className="mt-2 flex items-center gap-2 text-xs text-purple-600 dark:text-purple-400">
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span>交叉维度存在显著影响，建议查看详情</span>
        </div>
      )}
    </div>
  );
};

// 维度对比图表
interface DimensionChartProps {
  results: SingleDimensionResult[];
}

const DimensionChart: React.FC<DimensionChartProps> = ({ results }) => {
  const maxValue = Math.max(...results.map(r => r.entropy_reduction_normalized));

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
        维度熵减对比
      </h4>
      <div className="space-y-3">
        {results.map((result) => {
          const percentage = maxValue > 0 
            ? (result.entropy_reduction_normalized / maxValue) * 100 
            : 0;
          const isKeyDimension = result.is_key_dimension;

          return (
            <div key={result.dimension} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className={cn(
                  "font-medium",
                  isKeyDimension ? "text-blue-700 dark:text-blue-400" : "text-gray-600 dark:text-gray-400"
                )}>
                  {result.dimension}
                  {isKeyDimension && (
                    <span className="ml-1 text-blue-500">★</span>
                  )}
                </span>
                <span className={cn(
                  isKeyDimension ? "text-blue-600 dark:text-blue-400" : "text-gray-500 dark:text-gray-500"
                )}>
                  {(result.entropy_reduction_normalized * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    isKeyDimension 
                      ? "bg-gradient-to-r from-blue-500 to-indigo-500" 
                      : "bg-gray-300 dark:bg-gray-600"
                  )}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>熵: {result.entropy.toFixed(3)}</span>
                <span>{result.num_categories} 个类别</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// 维度详细分析
interface DimensionDetailsProps {
  results: SingleDimensionResult[];
  onDrillDown?: (dimension: string, child: string) => void;
}

const DimensionDetails: React.FC<DimensionDetailsProps> = ({ results, onDrillDown }) => {
  const [expandedDimension, setExpandedDimension] = React.useState<string | null>(
    results.find(r => r.is_key_dimension)?.dimension || null
  );

  return (
    <div className="space-y-3">
      {results.map((result) => {
        const isExpanded = expandedDimension === result.dimension;
        
        return (
          <div
            key={result.dimension}
            className={cn(
              "rounded-lg border transition-all",
              result.is_key_dimension
                ? "border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10"
                : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
            )}
          >
            {/* 头部 */}
            <button
              onClick={() => setExpandedDimension(isExpanded ? null : result.dimension)}
              className="w-full px-4 py-3 flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <span className={cn(
                  "text-sm font-medium",
                  result.is_key_dimension ? "text-blue-700 dark:text-blue-400" : "text-gray-700 dark:text-gray-300"
                )}>
                  {result.dimension}
                </span>
                {result.is_key_dimension && (
                  <span className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 text-xs rounded">
                    推荐
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  {(result.entropy_reduction_normalized * 100).toFixed(1)}%
                </span>
                <svg
                  className={cn(
                    "w-4 h-4 text-gray-400 transition-transform",
                    isExpanded && "rotate-180"
                  )}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>

            {/* 展开内容 */}
            {isExpanded && (
              <div className="px-4 pb-4">
                <div className="space-y-2">
                  {result.child_details.map((child) => (
                    <div
                      key={child.child_name}
                      className={cn(
                        "flex items-center justify-between p-2 rounded-lg text-xs",
                        child.child_name === result.top_child
                          ? "bg-blue-100 dark:bg-blue-900/30"
                          : "bg-gray-50 dark:bg-gray-700/50"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <span className={cn(
                          "font-medium",
                          child.child_name === result.top_child
                            ? "text-blue-700 dark:text-blue-400"
                            : "text-gray-700 dark:text-gray-300"
                        )}>
                          {child.child_name}
                        </span>
                        {child.child_name === result.top_child && (
                          <span className="text-blue-500">★</span>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={cn(
                          child.signed_contribution < 0 
                            ? "text-red-600 dark:text-red-400" 
                            : "text-green-600 dark:text-green-400"
                        )}>
                          {child.signed_contribution > 0 ? '+' : ''}
                          {(child.signed_contribution / 10000).toFixed(1)}万
                        </span>
                        <span className="text-gray-400">({(child.share * 100).toFixed(1)}%)</span>
                        {onDrillDown && child.child_name === result.top_child && (
                          <button
                            onClick={() => onDrillDown(result.dimension, child.child_name)}
                            className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
                          >
                            下钻
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* 统计信息 */}
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 flex gap-4 text-xs text-gray-500">
                  <span>类别数: {result.num_categories}</span>
                  <span>熵值: {result.entropy.toFixed(3)}</span>
                  <span>最大熵: {result.max_entropy.toFixed(3)}</span>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default EntropyResultPanel;
