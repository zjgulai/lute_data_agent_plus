import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
/// <reference types="vite/client" />
import type { TaskState } from '../../types';
import { useSessionStore } from '../../stores/sessionStore';
import { ApiTester } from '../debug/ApiTester';
import { EntropyResultPanel } from '../analysis/EntropyResultPanel';
import { CrossDimensionPanel } from '../analysis/CrossDimensionPanel';
import { FileUpload } from '../common/FileUpload';
import { exportApi } from '../../services/api';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * 节点详情组件
 * 
 * 根据当前状态显示不同的详情内容：
 * - 分析中：显示计算进度
 * - 等待输入：显示结构化表单
 * - 报告完成：显示最终报告
 */
export const NodeDetail: React.FC = () => {
  const { currentTask, selectedNodeId, lastEntropyResult, isAnalyzing } = useSessionStore();
  
  if (!currentTask) {
    return <EmptyState />;
  }
  
  const { state } = currentTask;
  
  // 根据状态渲染不同内容
  if (state === 'HUMAN_INPUT') {
    return <ConclusionForm />;
  }
  
  if (state === 'FINAL_REPORT') {
    return <FinalReport />;
  }
  
  if (state.includes('STEP') || state.includes('EXPLAIN') || state.includes('NARRATIVE')) {
    return <AnalysisProgress state={state} />;
  }
  
  // 默认显示节点信息和熵减分析结果
  return (
    <div className="h-full overflow-y-auto">
      <NodeInfo nodeId={selectedNodeId} />
      
      {/* 熵减分析结果 */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4 space-y-4">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          熵减分析
        </h3>
        <EntropyResultPanel
          results={lastEntropyResult?.results || []}
          selectedDimension={lastEntropyResult?.selectedDimension || null}
          selectedChild={lastEntropyResult?.selectedChild || null}
          isLoading={isAnalyzing}
          crossDimensionSignificant={lastEntropyResult?.crossDimension?.results.some((r) => r.is_significant)}
        />
        <CrossDimensionPanel
          crossDimension={lastEntropyResult?.crossDimension || null}
          isLoading={isAnalyzing}
        />
      </div>
    </div>
  );
};

// 空状态
const EmptyState: React.FC = () => (
  <div className="flex flex-col h-full">
    <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
      <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
        未选择节点
      </h3>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        点击指标树中的节点查看详情，<br />或点击"开始分析"启动归因任务
      </p>
    </div>
    
    {/* API 测试器（仅在开发环境显示） */}
    {import.meta.env.DEV && (
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <ApiTester />
      </div>
    )}
  </div>
);

// 节点信息
const NodeInfo: React.FC<{ nodeId: string | null }> = ({ nodeId }) => {
  const { drillDownHistory, goBack, resetDrillDown, currentTask } = useSessionStore();
  
  if (!nodeId) return null;
  
  // 获取当前节点的层级
  const currentLevel = drillDownHistory.find(h => h.nodeId === nodeId);
  
  return (
    <div className="p-4 space-y-4">
      {/* 面包屑导航 */}
      {drillDownHistory.length > 0 && (
        <div className="flex items-center gap-1 text-xs text-gray-500 flex-wrap">
          <button 
            onClick={resetDrillDown}
            className="hover:text-blue-600 transition-colors"
          >
            GMV
          </button>
          {drillDownHistory.map((record, index) => (
            <React.Fragment key={record.nodeId}>
              <svg className="w-3 h-3 mx-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              {index === drillDownHistory.length - 1 ? (
                <span className="text-blue-600 font-medium">{record.nodeName}</span>
              ) : (
                <button 
                  onClick={() => {
                    // 回退到该层级
                    const stepsToGoBack = drillDownHistory.length - index - 1;
                    for (let i = 0; i < stepsToGoBack; i++) {
                      goBack();
                    }
                  }}
                  className="hover:text-blue-600 transition-colors"
                >
                  {record.nodeName}
                </button>
              )}
            </React.Fragment>
          ))}
        </div>
      )}
      
      <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
        <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
          当前节点
        </span>
        <div className="flex items-center justify-between mt-1">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {currentLevel?.nodeName || nodeId}
          </h2>
          {drillDownHistory.length > 0 && (
            <button
              onClick={goBack}
              className="text-xs text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              返回
            </button>
          )}
        </div>
      </div>
      
      {/* 节点属性 */}
      <div className="space-y-3">
        <InfoRow label="节点ID" value={nodeId} />
        <InfoRow label="节点类型" value={currentLevel ? '分析节点' : '经营指标'} />
        <InfoRow label="层级" value={`L${drillDownHistory.length}`} />
        <InfoRow label="熵减阈值" value="0.2" />
        {currentTask && (
          <InfoRow 
            label="分析时段" 
            value={`${currentTask.analysis_period.start_date} 至 ${currentTask.analysis_period.end_date}`} 
          />
        )}
      </div>
    </div>
  );
};

// 信息行
const InfoRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="flex justify-between items-center">
    <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
    <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[200px]">{value}</span>
  </div>
);

// 分析进度
const AnalysisProgress: React.FC<{ state: TaskState }> = ({ state }) => {
  const getProgress = () => {
    if (state.includes('STEP1') || state.includes('EXPLAIN1')) return 25;
    if (state.includes('STEP2') || state.includes('EXPLAIN2')) return 50;
    if (state.includes('STEP3') || state.includes('EXPLAIN3')) return 75;
    if (state.includes('STEP4') || state.includes('EXPLAIN4')) return 90;
    if (state.includes('NARRATIVE')) return 95;
    return 0;
  };
  
  const progress = getProgress();
  
  return (
    <div className="p-4 space-y-4">
      <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">
          分析进行中
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          系统正在执行算法计算...
        </p>
      </div>
      
      {/* 进度条 */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-gray-500 dark:text-gray-400">进度</span>
          <span className="font-medium text-gray-900 dark:text-white">{progress}%</span>
        </div>
        <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      
      {/* 当前步骤 */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-blue-700 dark:text-blue-300">
            {getStepDescription(state)}
          </span>
        </div>
      </div>
    </div>
  );
};

// 获取步骤描述
const getStepDescription = (state: TaskState): string => {
  if (state.includes('STEP1')) return '正在计算 GMV 第一层拆解...';
  if (state.includes('EXPLAIN1')) return '步骤 1 完成，等待确认';
  if (state.includes('STEP2')) return '正在计算子维度熵减...';
  if (state.includes('EXPLAIN2')) return '步骤 2 完成，等待确认';
  if (state.includes('STEP3')) return '正在定位动作指标...';
  if (state.includes('EXPLAIN3')) return '步骤 3 完成，等待确认';
  if (state.includes('STEP4')) return '正在汇总归因结果...';
  if (state.includes('EXPLAIN4')) return '步骤 4 完成，等待确认';
  if (state.includes('NARRATIVE')) return '正在生成 LLM 叙事报告...';
  return '分析中...';
};

// 结论表单
const ConclusionForm: React.FC = () => {
  const { submitConclusion, isLoading, currentTask } = useSessionStore();
  const [formData, setFormData] = React.useState({
    reason_type: '',
    detailed_explanation: '',
    involved_departments: [] as string[],
    suggested_actions: '',
    confidence_level: 'medium' as 'high' | 'medium' | 'low',
  });
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await submitConclusion({
      ...formData,
      involved_departments: formData.involved_departments,
    });
  };
  
  return (
    <form onSubmit={handleSubmit} className="p-4 space-y-4">
      <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">
          补充业务结论
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          基于算法分析结果，请补充您的业务洞察
        </p>
      </div>
      
      {/* 文件上传 */}
      {currentTask && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300">
            参考文件
          </h4>
          <FileUpload sessionId={currentTask.task_id} />
        </div>
      )}
      
      {/* 原因类型 */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
          原因类型
        </label>
        <select
          value={formData.reason_type}
          onChange={(e) => setFormData({ ...formData, reason_type: e.target.value })}
          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
        >
          <option value="">请选择原因类型</option>
          <option value="budget_cut">预算削减</option>
          <option value="competitor">竞品动作</option>
          <option value="policy_change">政策变化</option>
          <option value="seasonal">季节性因素</option>
          <option value="product_issue">产品问题</option>
          <option value="marketing_issue">营销问题</option>
          <option value="other">其他</option>
        </select>
      </div>
      
      {/* 详细说明 */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
          详细说明
        </label>
        <textarea
          value={formData.detailed_explanation}
          onChange={(e) => setFormData({ ...formData, detailed_explanation: e.target.value })}
          rows={4}
          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          placeholder="请详细描述导致指标波动的业务原因..."
          required
        />
      </div>
      
      {/* 涉及部门 */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
          涉及部门
        </label>
        <div className="flex flex-wrap gap-2">
          {['市场部', '销售部', '产品部', '运营部', '财务部'].map((dept) => (
            <button
              key={dept}
              type="button"
              onClick={() => {
                const newDepts = formData.involved_departments.includes(dept)
                  ? formData.involved_departments.filter(d => d !== dept)
                  : [...formData.involved_departments, dept];
                setFormData({ ...formData, involved_departments: newDepts });
              }}
              className={cn(
                "px-3 py-1 text-xs rounded-full border transition-colors",
                formData.involved_departments.includes(dept)
                  ? "bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300"
                  : "bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
              )}
            >
              {dept}
            </button>
          ))}
        </div>
      </div>
      
      {/* 建议行动 */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
          建议行动
        </label>
        <input
          type="text"
          value={formData.suggested_actions}
          onChange={(e) => setFormData({ ...formData, suggested_actions: e.target.value })}
          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="建议采取的行动措施..."
        />
      </div>
      
      {/* 置信度 */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-gray-700 dark:text-gray-300">
          置信度
        </label>
        <div className="flex gap-2">
          {[
            { value: 'high', label: '高', color: 'green' },
            { value: 'medium', label: '中', color: 'yellow' },
            { value: 'low', label: '低', color: 'red' },
          ].map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setFormData({ ...formData, confidence_level: option.value as any })}
              className={cn(
                "flex-1 py-2 text-xs font-medium rounded-lg border transition-colors",
                formData.confidence_level === option.value
                  ? `bg-${option.color}-100 dark:bg-${option.color}-900/30 border-${option.color}-300 dark:border-${option.color}-700 text-${option.color}-700 dark:text-${option.color}-300`
                  : "bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* 提交按钮 */}
      <button
        type="submit"
        disabled={isLoading}
        className={cn(
          "w-full py-2.5 px-4 rounded-lg text-sm font-medium transition-colors",
          "bg-blue-600 hover:bg-blue-700 text-white",
          "disabled:opacity-50 disabled:cursor-not-allowed"
        )}
      >
        {isLoading ? '提交中...' : '提交结论'}
      </button>
    </form>
  );
};

// 最终报告
const FinalReport: React.FC = () => {
  const { currentTask, drillDownHistory } = useSessionStore();
  const [isExporting, setIsExporting] = React.useState<{ word?: boolean; pdf?: boolean }>({});
  
  if (!currentTask) return null;
  
  const handleExport = async (format: 'word' | 'pdf', reportType: 'process' | 'full') => {
    setIsExporting(prev => ({ ...prev, [format]: true }));
    try {
      const blob = format === 'word'
        ? await exportApi.exportWord(currentTask.task_id, reportType)
        : await exportApi.exportPDF(currentTask.task_id, reportType);
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `gmv_attribution_${currentTask.task_id}_${reportType}.${format === 'word' ? 'docx' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('导出失败:', err);
      alert(err instanceof Error ? err.message : '导出失败');
    } finally {
      setIsExporting(prev => ({ ...prev, [format]: false }));
    }
  };
  
  return (
    <div className="p-4 space-y-4">
      <div className="border-b border-gray-200 dark:border-gray-700 pb-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            归因报告
          </h3>
        </div>
      </div>
      
      {/* 执行摘要 */}
      <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
        <h4 className="text-xs font-medium text-green-800 dark:text-green-300 mb-2">
          执行摘要
        </h4>
        <p className="text-xs text-green-700 dark:text-green-400 leading-relaxed">
          2026年3月 GMV 环比下滑 20%（-200万），主要原因是美国市场 A 产品线上广告投放预算削减 35%，导致 UV 下降 20%。
        </p>
      </div>
      
      {/* 归因链 */}
      <div className="space-y-2">
        <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300">
          归因路径
        </h4>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
            GMV
          </span>
          {drillDownHistory.map((record) => (
            <React.Fragment key={record.nodeId}>
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                {record.nodeName}
              </span>
            </React.Fragment>
          ))}
          {!drillDownHistory.length && currentTask?.attribution_chain.map((node) => (
            <React.Fragment key={node.node_id}>
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">
                {node.node_name}
              </span>
            </React.Fragment>
          ))}
        </div>
      </div>
      
      {/* 导出按钮 */}
      <div className="pt-4 space-y-2">
        <button
          onClick={() => handleExport('word', 'process')}
          disabled={isExporting.word}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {isExporting.word ? (
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          )}
          导出 Word 过程报告
        </button>
        <button
          onClick={() => handleExport('pdf', 'full')}
          disabled={isExporting.pdf}
          className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          {isExporting.pdf ? (
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          )}
          导出 PDF 完整报告
        </button>
      </div>
    </div>
  );
};
