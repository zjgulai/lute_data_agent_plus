import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useSessionStore } from '../../stores/sessionStore';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 归因链组件
 * 
 * 显示从 GMV 根节点到当前分析节点的完整下钻路径。
 * 每个节点卡片展示：节点名称、选择的维度、熵减值、贡献度。
 * 支持点击回退到任意历史节点。
 */
export const AttributionChain: React.FC = () => {
  const { 
    drillDownHistory, 
    currentTask, 
    goBack, 
    resetDrillDown,
    selectedNodeId,
    selectNode,
  } = useSessionStore();

  // 构建完整的归因链节点列表
  const chainItems = React.useMemo(() => {
    const items: Array<{
      id: string;
      name: string;
      type: 'root' | 'drill';
      dimension?: string | null;
      child?: string | null;
      entropy?: number;
      contribution?: number;
      isCurrent: boolean;
    }> = [
      {
        id: 'gmv',
        name: 'GMV',
        type: 'root',
        isCurrent: selectedNodeId === 'gmv' || (!selectedNodeId && drillDownHistory.length === 0),
      },
    ];

    drillDownHistory.forEach((record, index) => {
      const isLast = index === drillDownHistory.length - 1;
      const topResult = record.entropyResults[0];
      items.push({
        id: record.nodeId,
        name: record.nodeName,
        type: 'drill',
        dimension: record.selectedDimension,
        child: record.selectedChild,
        entropy: topResult?.entropy_reduction_normalized,
        contribution: topResult?.child_details.find(
          c => c.child_name === record.selectedChild
        )?.signed_contribution,
        isCurrent: isLast || selectedNodeId === record.nodeId,
      });
    });

    return items;
  }, [drillDownHistory, selectedNodeId]);

  // 如果没有任务且没有下钻历史，显示引导态
  if (!currentTask && chainItems.length <= 1) {
    return (
      <div className="flex items-center justify-center h-full text-xs text-gray-400">
        启动分析后将在此展示归因路径
      </div>
    );
  }

  const handleNodeClick = (index: number) => {
    if (index === 0) {
      resetDrillDown();
      selectNode('gmv');
      return;
    }
    
    // 回退到指定层级
    const stepsToGoBack = drillDownHistory.length - index;
    if (stepsToGoBack > 0) {
      for (let i = 0; i < stepsToGoBack; i++) {
        goBack();
      }
    }
    const targetId = chainItems[index]?.id;
    if (targetId) selectNode(targetId);
  };

  return (
    <div className="h-full flex flex-col">
      {/* 水平滚动的归因链 */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden">
        <div className="flex items-center h-full px-2 min-w-max">
          {chainItems.map((item, index) => (
            <React.Fragment key={item.id}>
              {/* 节点卡片 */}
              <button
                onClick={() => handleNodeClick(index)}
                className={cn(
                  "relative flex flex-col justify-center px-4 py-2 rounded-lg border min-w-[120px] max-w-[180px] transition-all",
                  "text-left hover:shadow-sm",
                  item.isCurrent
                    ? "bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700"
                    : "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-700"
                )}
              >
                {/* 节点名称 */}
                <span className={cn(
                  "text-sm font-medium truncate",
                  item.isCurrent
                    ? "text-blue-700 dark:text-blue-300"
                    : "text-gray-900 dark:text-white"
                )}>
                  {item.name}
                </span>

                {/* 维度信息 */}
                {item.dimension && (
                  <span className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
                    经 {item.dimension}
                  </span>
                )}

                {/* 指标数据 */}
                <div className="flex items-center gap-2 mt-1.5">
                  {item.entropy !== undefined && (
                    <span className="text-[10px] px-1.5 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded">
                      熵减 {formatPercent(item.entropy)}
                    </span>
                  )}
                  {item.contribution !== undefined && (
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded",
                      item.contribution < 0
                        ? "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300"
                        : "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300"
                    )}>
                      {formatNumber(item.contribution)}
                    </span>
                  )}
                </div>

                {/* 当前节点指示器 */}
                {item.isCurrent && (
                  <div className="absolute -top-1.5 -right-1.5 w-3 h-3 bg-blue-500 rounded-full border-2 border-white dark:border-gray-800" />
                )}
              </button>

              {/* 连接箭头 */}
              {index < chainItems.length - 1 && (
                <div className="flex items-center px-2">
                  <svg
                    className="w-5 h-5 text-gray-300 dark:text-gray-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* 操作栏 */}
      <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-800/50">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          共 <span className="font-medium text-gray-700 dark:text-gray-300">{chainItems.length}</span> 个节点
          {drillDownHistory.length > 0 && (
            <span className="ml-2">
              下钻深度: <span className="font-medium text-gray-700 dark:text-gray-300">L{drillDownHistory.length}</span>
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {drillDownHistory.length > 0 && (
            <button
              onClick={() => {
                resetDrillDown();
                selectNode('gmv');
              }}
              className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
            >
              重置路径
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value: number): string {
  if (Math.abs(value) >= 10000) {
    return `${(value / 10000).toFixed(1)}万`;
  }
  return `${Math.round(value)}`;
}
