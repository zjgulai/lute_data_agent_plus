import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { TaskState } from '../../types';
import { useSessionStore } from '../../stores/sessionStore';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Step {
  id: number;
  title: string;
  description: string;
  states: TaskState[];
}

const STEPS: Step[] = [
  {
    id: 1,
    title: '第一层拆解',
    description: 'GMV 维度熵减计算',
    states: ['AUTO_STEP1', 'MANUAL_STEP1', 'LLM_EXPLAIN_1'],
  },
  {
    id: 2,
    title: '子维度分析',
    description: '关键维度下钻',
    states: ['AUTO_STEP2', 'MANUAL_STEP2', 'LLM_EXPLAIN_2'],
  },
  {
    id: 3,
    title: '动作指标定位',
    description: '定位具体业务动作',
    states: ['AUTO_STEP3', 'MANUAL_STEP3', 'LLM_EXPLAIN_3'],
  },
  {
    id: 4,
    title: '结论汇总',
    description: '生成归因报告',
    states: ['AUTO_STEP4', 'AUTO_SUMMARY', 'MANUAL_STEP4', 'LLM_EXPLAIN_4', 'LLM_NARRATIVE', 'HUMAN_INPUT', 'FINAL_REPORT'],
  },
];

/**
 * 步骤时间轴组件
 * 
 * 显示归因分析的4个步骤进度
 */
export const StepTimeline: React.FC = () => {
  const { currentTask, continueTask, isLoading, highlightStepPath } = useSessionStore();
  
  if (!currentTask) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
        点击"开始分析"启动新的归因任务
      </div>
    );
  }
  
  const currentState = currentTask.state;
  const isManual = currentTask.mode === 'manual';
  
  // 判断步骤是否完成
  const isStepCompleted = (step: Step): boolean => {
    const currentStepIndex = STEPS.findIndex(s => s.states.includes(currentState));
    const stepIndex = STEPS.indexOf(step);
    return stepIndex < currentStepIndex;
  };
  
  // 判断步骤是否正在进行
  const isStepActive = (step: Step): boolean => {
    return step.states.includes(currentState);
  };
  
  // 判断是否可以点击步骤
  const canClickStep = (step: Step): boolean => {
    if (isLoading) return false;
    if (!isManual) return false; // 自动模式下不能点击
    
    const currentStepIndex = STEPS.findIndex(s => s.states.includes(currentState));
    const stepIndex = STEPS.indexOf(step);
    
    // 只能点击当前步骤的下一个（在 LLM_EXPLAIN 状态）
    if (currentState.startsWith('LLM_EXPLAIN_')) {
      return stepIndex === currentStepIndex;
    }
    
    return false;
  };
  
  const handleStepClick = async (step: Step) => {
    if (!canClickStep(step)) return;
    // 联动高亮路径
    highlightStepPath(step.id - 1);
    await continueTask();
  };
  
  return (
    <div className="space-y-4">
      {STEPS.map((step, index) => {
        const completed = isStepCompleted(step);
        const active = isStepActive(step);
        const clickable = canClickStep(step);
        
        return (
          <div
            key={step.id}
            className={cn(
              "relative flex gap-4",
              clickable && "cursor-pointer"
            )}
            onClick={() => handleStepClick(step)}
          >
            {/* 连接线 */}
            {index < STEPS.length - 1 && (
              <div
                className={cn(
                  "absolute left-[19px] top-10 w-0.5 h-8",
                  completed ? "bg-blue-500" : "bg-gray-200 dark:bg-gray-700"
                )}
              />
            )}
            
            {/* 步骤图标 */}
            <div
              className={cn(
                "relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-colors",
                completed && "bg-blue-500 text-white",
                active && !completed && "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border-2 border-blue-500",
                !completed && !active && "bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500"
              )}
            >
              {completed ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <span className="text-sm font-medium">{step.id}</span>
              )}
            </div>
            
            {/* 步骤内容 */}
            <div className={cn(
              "flex-1 pb-6",
              active && !completed && "opacity-100",
              !active && !completed && "opacity-60"
            )}>
              <h3
                className={cn(
                  "text-sm font-medium",
                  active || completed
                    ? "text-gray-900 dark:text-white"
                    : "text-gray-500 dark:text-gray-400"
                )}
              >
                {step.title}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {step.description}
              </p>
              
              {/* 当前步骤状态 */}
              {active && (
                <div className="mt-2">
                  <StepStateBadge state={currentState} />
                </div>
              )}
              
              {/* 继续按钮（手动模式下） */}
              {active && clickable && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStepClick(step);
                  }}
                  disabled={isLoading}
                  className={cn(
                    "mt-3 px-3 py-1.5 text-xs font-medium rounded-md transition-colors",
                    "bg-blue-600 hover:bg-blue-700 text-white",
                    "disabled:opacity-50 disabled:cursor-not-allowed"
                  )}
                >
                  {isLoading ? '处理中...' : '继续'}
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// 步骤状态徽章
const StepStateBadge: React.FC<{ state: TaskState }> = ({ state }) => {
  const getBadgeStyle = () => {
    if (state.includes('STEP')) {
      return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300';
    }
    if (state.includes('EXPLAIN')) {
      return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300';
    }
    if (state.includes('NARRATIVE')) {
      return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300';
    }
    if (state === 'HUMAN_INPUT') {
      return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300';
    }
    if (state === 'FINAL_REPORT') {
      return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300';
    }
    return 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400';
  };
  
  const getBadgeText = () => {
    if (state.includes('STEP')) return '计算中';
    if (state.includes('EXPLAIN')) return '等待确认';
    if (state.includes('NARRATIVE')) return '生成叙事';
    if (state === 'HUMAN_INPUT') return '等待输入';
    if (state === 'FINAL_REPORT') return '完成';
    return state;
  };
  
  return (
    <span className={cn(
      "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
      getBadgeStyle()
    )}>
      {getBadgeText()}
    </span>
  );
};

// 任务创建按钮
export const TaskCreateButton: React.FC = () => {
  const [mode, setMode] = React.useState<'auto' | 'manual'>('auto');
  const { createTask, isLoading } = useSessionStore();
  
  const handleCreate = async () => {
    const today = new Date();
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const endOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
    
    await createTask(
      mode,
      lastMonth.toISOString().split('T')[0],
      endOfLastMonth.toISOString().split('T')[0]
    );
  };
  
  return (
    <div className="space-y-3">
      <div className="flex gap-2 p-1 bg-gray-100 dark:bg-gray-700 rounded-lg">
        <button
          onClick={() => setMode('auto')}
          className={cn(
            "flex-1 py-1.5 px-3 text-xs font-medium rounded-md transition-colors",
            mode === 'auto'
              ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
              : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          )}
        >
          自动模式
        </button>
        <button
          onClick={() => setMode('manual')}
          className={cn(
            "flex-1 py-1.5 px-3 text-xs font-medium rounded-md transition-colors",
            mode === 'manual'
              ? "bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm"
              : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          )}
        >
          手动模式
        </button>
      </div>
      
      <button
        onClick={handleCreate}
        disabled={isLoading}
        className={cn(
          "w-full py-2 px-4 rounded-lg text-sm font-medium transition-colors",
          "bg-blue-600 hover:bg-blue-700 text-white",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "flex items-center justify-center gap-2"
        )}
      >
        {isLoading ? (
          <>
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            创建中...
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            开始分析
          </>
        )}
      </button>
      
      <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
        {mode === 'auto' 
          ? '自动模式：3-5秒完成全部分析' 
          : '手动模式：每步暂停等待确认'}
      </p>
    </div>
  );
};
