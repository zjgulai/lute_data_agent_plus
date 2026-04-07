import { useState, useCallback, useEffect } from 'react';
import { ThreeColumnLayout } from './components/layout/ThreeColumnLayout';
import { StepTimeline, TaskCreateButton } from './components/timeline/StepTimeline';
import { MermaidTree } from './components/tree/MermaidTree';
import { NodeDetail } from './components/detail/NodeDetail';
import { RoleSwitcher } from './components/permission/RoleSwitcher';
import { useSessionStore } from './stores/sessionStore';
import { generateSampleMermaidCode } from './components/tree/MermaidTree';
import { AttributionChain } from './components/chain/AttributionChain';
import { GMVTimeline } from './components/timeline-d3/GMVTimeline';
import './App.css';

function App() {
  const { 
    currentTask, 
    selectedNodeId, 
    selectNode, 
    mermaidCode, 
    loadTreePreview,
    error,
    setError,
    drillDown,
    lastEntropyResult,
    isAnalyzing,
    currentUser,
    highlightedPath,
  } = useSessionStore();
  
  // 获取指标树数据
  const indicatorTree = currentTask?.indicator_tree?.root || null;
  const [displayCode, setDisplayCode] = useState<string>('');
  const [isLoadingTree, setIsLoadingTree] = useState(false);
  
  // 初始化加载指标树
  useEffect(() => {
    const initTree = async () => {
      if (!mermaidCode && !currentTask) {
        setIsLoadingTree(true);
        try {
          await loadTreePreview();
        } catch (err) {
          console.error('加载指标树失败:', err);
          setDisplayCode(generateSampleMermaidCode());
        } finally {
          setIsLoadingTree(false);
        }
      }
    };
    
    initTree();
  }, [mermaidCode, currentTask, loadTreePreview]);
  
  // 更新显示的 Mermaid 代码
  useEffect(() => {
    if (mermaidCode) {
      setDisplayCode(mermaidCode);
    } else if (!currentTask && !isLoadingTree) {
      setDisplayCode(generateSampleMermaidCode());
    }
  }, [mermaidCode, currentTask, isLoadingTree]);
  
  // 处理节点点击 - 执行下钻分析
  const handleNodeClick = useCallback(async (nodeId: string) => {
    selectNode(nodeId);
    
    // 如果有任务，执行下钻分析
    if (currentTask) {
      // 模拟维度池和数据（实际应从指标树配置和 Excel 数据获取）
      const dimensionPool = [
        { dimension_name: '区域', dimension_id: 'region', child_nodes: ['美国', '中国', '欧洲', '亚太'] },
        { dimension_name: '产品', dimension_id: 'product', child_nodes: ['产品A', '产品B', '产品C'] },
        { dimension_name: '渠道', dimension_id: 'channel', child_nodes: ['线上', '线下'] },
      ];
      
      // 模拟数据（实际应从后端数据服务获取）
      const rawData: Record<string, number> = {
        '美国': -1980000,
        '中国': 100000,
        '欧洲': -120000,
        '亚太': 0,
        '产品A': -1200000,
        '产品B': -800000,
        '产品C': 10000,
        '线上': 0,
        '线下': 0,
      };
      
      try {
        await drillDown(nodeId, nodeId, dimensionPool, rawData);
      } catch (err) {
        console.error('下钻分析失败:', err);
      }
    }
  }, [selectNode, currentTask, drillDown]);
  
  // 刷新图表
  const handleRefreshTree = async () => {
    setIsLoadingTree(true);
    try {
      await loadTreePreview();
    } catch (err) {
      console.error('刷新指标树失败:', err);
      setDisplayCode(generateSampleMermaidCode());
    } finally {
      setIsLoadingTree(false);
    }
  };
  
  // 清除错误
  const handleDismissError = () => {
    setError(null);
  };
  
  // 左栏内容
  const leftPanel = (
    <div className="space-y-6">
      {/* 错误提示 */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-red-600 dark:text-red-400">{error}</p>
            </div>
            <button 
              onClick={handleDismissError}
              className="text-red-400 hover:text-red-600"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
      
      {/* 任务创建按钮（未开始任务时显示） */}
      {!currentTask && <TaskCreateButton />}
      
      {/* 步骤时间轴 */}
      <StepTimeline />
      
      {/* GMV 时间轴 */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
          GMV 趋势
        </h4>
        <GMVTimeline width={256} height={160} />
      </div>
      
      {/* 分析周期信息 */}
      {currentTask && (
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
            分析周期
          </h4>
          <div className="text-xs text-gray-700 dark:text-gray-300 space-y-1">
            <div className="flex justify-between">
              <span>开始日期</span>
              <span>{currentTask.analysis_period.start_date}</span>
            </div>
            <div className="flex justify-between">
              <span>结束日期</span>
              <span>{currentTask.analysis_period.end_date}</span>
            </div>
            <div className="flex justify-between">
              <span>对比周期</span>
              <span>{getComparisonPeriodText(currentTask.analysis_period.comparison_period)}</span>
            </div>
          </div>
        </div>
      )}
      
      {/* 会话信息 */}
      {currentTask && (
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
            会话信息
          </h4>
          <div className="text-xs text-gray-700 dark:text-gray-300 space-y-1">
            <div className="flex justify-between">
              <span>会话 ID</span>
              <span className="font-mono text-xs truncate max-w-[100px]">{currentTask.task_id}</span>
            </div>
            <div className="flex justify-between">
              <span>当前节点</span>
              <span className="truncate max-w-[100px]">{currentTask.current_node_id}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
  
  // 中栏内容
  const centerPanel = (
    <div className="h-full flex flex-col">
      {/* 工具栏 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            当前选中: {selectedNodeId || 'GMV'}
          </span>
          {currentTask && (
            <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
              {currentTask.task_id}
            </span>
          )}
          {isAnalyzing && (
            <span className="text-xs px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full flex items-center gap-1">
              <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              分析中
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* 角色切换器（开发模式） */}
          {import.meta.env.DEV && <RoleSwitcher />}
          
          <button 
            onClick={handleRefreshTree}
            disabled={isLoadingTree || isAnalyzing}
            className="px-3 py-1.5 text-xs bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            {isLoadingTree ? (
              <>
                <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                加载中...
              </>
            ) : (
              <>
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                刷新
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* Mermaid 图表 */}
      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 overflow-auto">
        {displayCode || (indicatorTree && currentUser) ? (
          <MermaidTree
            mermaidCode={indicatorTree && currentUser ? undefined : displayCode}
            tree={indicatorTree || undefined}
            user={currentUser}
            enablePermissionFilter={!!(indicatorTree && currentUser)}
            selectedNodeId={selectedNodeId}
            highlightedPath={highlightedPath}
            onNodeClick={handleNodeClick}
            className="w-full h-full min-h-[400px]"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            {isLoadingTree ? '加载指标树...' : '暂无数据'}
          </div>
        )}
      </div>
      
      {/* 图例 */}
      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs">
        <span className="text-gray-500 dark:text-gray-400">图例:</span>
        <LegendItem color="bg-blue-500" label="根节点" />
        <LegendItem color="bg-red-500" label="组织侧" />
        <LegendItem color="bg-green-500" label="经营侧" />
        <LegendItem color="bg-purple-500" label="动作指标" />
      </div>
      
      {/* 下钻建议提示 */}
      {lastEntropyResult?.selectedDimension && !isAnalyzing && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-xs text-blue-700 dark:text-blue-300">
                建议从「{lastEntropyResult.selectedDimension}」维度下钻到「{lastEntropyResult.selectedChild}」
              </span>
            </div>
            <button 
              onClick={() => {
                if (lastEntropyResult.selectedChild) {
                  handleNodeClick(lastEntropyResult.selectedChild);
                }
              }}
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
            >
              下钻
            </button>
          </div>
        </div>
      )}
    </div>
  );
  
  // 右栏内容
  const rightPanel = <NodeDetail />;
  
  // 底部归因链
  const bottomPanel = <AttributionChain />;
  
  return (
    <ThreeColumnLayout
      leftPanel={leftPanel}
      centerPanel={centerPanel}
      rightPanel={rightPanel}
      bottomPanel={bottomPanel}
    />
  );
}

// 图例项组件
const LegendItem: React.FC<{ color: string; label: string }> = ({ color, label }) => (
  <div className="flex items-center gap-1.5">
    <div className={`w-3 h-3 rounded ${color}`} />
    <span className="text-gray-600 dark:text-gray-400">{label}</span>
  </div>
);

// 获取对比周期文本
const getComparisonPeriodText = (period: string): string => {
  const periodMap: Record<string, string> = {
    'prev_month': '上月',
    'prev_quarter': '上季度',
    'prev_year': '去年同期',
  };
  return periodMap[period] || period;
};

export default App;
