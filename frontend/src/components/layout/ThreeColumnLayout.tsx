import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useSessionStore } from '../../stores/sessionStore';

// 工具函数：合并 tailwind 类名
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ThreeColumnLayoutProps {
  // 左栏：时间轴
  leftPanel: React.ReactNode;
  // 中栏：指标树
  centerPanel: React.ReactNode;
  // 右栏：节点详情
  rightPanel: React.ReactNode;
  // 底部：归因链
  bottomPanel?: React.ReactNode;
  // 自定义类名
  className?: string;
}

/**
 * 三栏式布局组件
 * 
 * 布局结构：
 * - 左栏：归因时间轴（Steps 1-4）
 * - 中栏：可视化指标树（Mermaid.js）
 * - 右栏：节点详情区（数据/表单/报告）
 * - 底部：归因链汇总框（可选）
 */
export const ThreeColumnLayout: React.FC<ThreeColumnLayoutProps> = ({
  leftPanel,
  centerPanel,
  rightPanel,
  bottomPanel,
  className,
}) => {
  return (
    <div className={cn("flex flex-col h-screen bg-gray-50 dark:bg-gray-900", className)}>
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 h-14 flex items-center px-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            GMV 智能归因系统
          </h1>
        </div>
        
        <div className="flex-1" />
        
        <div className="flex items-center gap-4">
          {/* 运行模式指示器 */}
          <ModeIndicator />
          
          {/* 用户头像 */}
          <UserAvatar />
        </div>
      </header>

      {/* Main Content - Three Columns */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Timeline */}
        <aside className="w-72 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              归因进度
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {leftPanel}
          </div>
        </aside>

        {/* Center Panel - Indicator Tree */}
        <main className="flex-1 flex flex-col min-w-0 bg-gray-50 dark:bg-gray-900">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              指标树
            </h2>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {centerPanel}
          </div>
        </main>

        {/* Right Panel - Node Details */}
        <aside className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              节点详情
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            {rightPanel}
          </div>
        </aside>
      </div>

      {/* Bottom Panel - Attribution Chain (可选) */}
      {bottomPanel && (
        <div className="h-48 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex flex-col shrink-0">
          <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              归因链
            </h3>
          </div>
          <div className="flex-1 overflow-x-auto overflow-y-hidden p-4">
            {bottomPanel}
          </div>
        </div>
      )}
    </div>
  );
};

// 运行模式指示器
const ModeIndicator: React.FC = () => {
  const { currentTask } = useSessionStore();
  
  if (!currentTask) {
    return (
      <span className="text-xs text-gray-500 dark:text-gray-400">
        未开始
      </span>
    );
  }
  
  const isAuto = currentTask.mode === 'auto';
  
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-700">
      <span className={cn(
        "w-2 h-2 rounded-full",
        isAuto ? "bg-green-500" : "bg-blue-500"
      )} />
      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
        {isAuto ? '自动模式' : '手动模式'}
      </span>
      <span className="text-xs text-gray-500 dark:text-gray-400">
        · {getStateDisplayName(currentTask.state)}
      </span>
    </div>
  );
};

// 用户头像
const UserAvatar: React.FC = () => {
  const { currentUser } = useSessionStore();
  
  if (!currentUser) return null;
  
  const roleLabels: Record<string, string> = {
    global_manager: '全局管理者',
    regional_manager: '区域管理者',
    business_user: '业务用户',
  };
  
  return (
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-medium">
        {currentUser.name.charAt(0)}
      </div>
      <div className="hidden sm:block text-xs">
        <div className="text-gray-900 dark:text-white font-medium">
          {currentUser.name}
        </div>
        <div className="text-gray-500 dark:text-gray-400">
          {roleLabels[currentUser.role] || currentUser.role}
        </div>
      </div>
    </div>
  );
};

// 状态显示名称
function getStateDisplayName(state: string): string {
  const stateNames: Record<string, string> = {
    'INIT': '初始化',
    'MODE_SELECT': '选择模式',
    'AUTO_STEP1': '步骤 1/4',
    'AUTO_STEP2': '步骤 2/4',
    'AUTO_STEP3': '步骤 3/4',
    'AUTO_STEP4': '步骤 4/4',
    'AUTO_SUMMARY': '汇总中',
    'MANUAL_STEP1': '步骤 1/4',
    'MANUAL_STEP2': '步骤 2/4',
    'MANUAL_STEP3': '步骤 3/4',
    'MANUAL_STEP4': '步骤 4/4',
    'LLM_EXPLAIN_1': '说明 1/4',
    'LLM_EXPLAIN_2': '说明 2/4',
    'LLM_EXPLAIN_3': '说明 3/4',
    'LLM_EXPLAIN_4': '说明 4/4',
    'LLM_NARRATIVE': '生成报告',
    'HUMAN_INPUT': '等待输入',
    'FINAL_REPORT': '报告完成',
    'ALGO_ERROR': '算法错误',
    'DATA_MISSING': '数据缺失',
  };
  return stateNames[state] || state;
}


