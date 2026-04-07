import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { AttributionTask, TaskState, AnalysisMode, EntropyResult, User, UserRole, TreeNode } from '../types';
import { sessionApi, algorithmApi, treeApi } from '../services/api';
import type { SingleDimensionResult, CrossDimensionResponse } from '../services/api';

// 下钻历史记录
interface DrillDownRecord {
  nodeId: string;
  nodeName: string;
  timestamp: string;
  entropyResults: SingleDimensionResult[];
  selectedDimension: string | null;
  selectedChild: string | null;
  crossDimension: CrossDimensionResponse | null;
}

interface SessionState {
  // 当前任务
  currentTask: AttributionTask | null;
  
  // 加载状态
  isLoading: boolean;
  error: string | null;
  
  // 当前用户
  currentUser: User | null;
  
  // 选中的节点
  selectedNodeId: string | null;
  
  // 熵减计算结果
  entropyResults: EntropyResult[] | null;
  
  // 指标树 Mermaid 代码
  mermaidCode: string | null;
  
  // 节点下钻相关
  drillDownHistory: DrillDownRecord[];
  currentAnalysisNode: TreeNode | null;
  isAnalyzing: boolean;
  lastEntropyResult: {
    results: SingleDimensionResult[];
    selectedDimension: string | null;
    selectedChild: string | null;
    crossDimension: CrossDimensionResponse | null;
  } | null;
  
  // 高亮路径（时间轴联动）
  highlightedPath: string[];
  
  // 操作
  setCurrentTask: (task: AttributionTask | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setCurrentUser: (user: User | null) => void;
  selectNode: (nodeId: string | null) => void;
  setEntropyResults: (results: EntropyResult[] | null) => void;
  setMermaidCode: (code: string | null) => void;
  
  // 任务操作
  createTask: (mode: AnalysisMode, startDate: string, endDate: string) => Promise<void>;
  continueTask: () => Promise<void>;
  submitConclusion: (conclusion: {
    reason_type: string;
    detailed_explanation: string;
    involved_departments: string[];
    suggested_actions: string;
    confidence_level: 'high' | 'medium' | 'low';
  }) => Promise<void>;
  refreshTaskStatus: () => Promise<void>;
  loadTreePreview: () => Promise<void>;
  
  // 节点下钻操作
  drillDown: (nodeId: string, nodeName: string, dimensionPool: Array<{
    dimension_name: string;
    dimension_id: string;
    child_nodes: string[];
  }>, rawData: Record<string, number>) => Promise<void>;
  refreshCrossDimension: (nodeId: string) => Promise<void>;
  goBack: () => void;
  resetDrillDown: () => void;
  highlightStepPath: (stepIndex: number) => void;
  
  // 权限检查
  canViewNode: (nodeId: string, permissionScope?: string[]) => boolean;
  isGlobalManager: () => boolean;
}

function convertBackendState(state: string): TaskState {
  const validStates: TaskState[] = [
    'INIT', 'MODE_SELECT',
    'AUTO_STEP1', 'AUTO_STEP2', 'AUTO_STEP3', 'AUTO_STEP4', 'AUTO_SUMMARY',
    'MANUAL_STEP1', 'MANUAL_STEP2', 'MANUAL_STEP3', 'MANUAL_STEP4',
    'LLM_EXPLAIN_1', 'LLM_EXPLAIN_2', 'LLM_EXPLAIN_3', 'LLM_EXPLAIN_4',
    'LLM_NARRATIVE', 'HUMAN_INPUT', 'FINAL_REPORT',
    'ALGO_ERROR', 'DATA_MISSING'
  ];
  
  if (validStates.includes(state as TaskState)) {
    return state as TaskState;
  }
  
  if (state === 'TERMINATED') return 'FINAL_REPORT';
  if (state === 'EXPORT_PROCESS') return 'FINAL_REPORT';
  
  return 'INIT';
}

export const useSessionStore = create<SessionState>()(
  devtools(
    (set, get) => ({
      // 初始状态
      currentTask: null,
      isLoading: false,
      error: null,
      currentUser: {
        id: 'user-001',
        name: '张经理',
        role: 'global_manager' as UserRole,
        assigned_regions: ['global'],
        permissions: ['view_all', 'export_reports', 'submit_conclusions'],
      },
      selectedNodeId: null,
      entropyResults: null,
      mermaidCode: null,
      drillDownHistory: [],
      currentAnalysisNode: null,
      isAnalyzing: false,
      lastEntropyResult: null,
      highlightedPath: [],
      
      // 基础设置
      setCurrentTask: (task) => set({ currentTask: task }),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      setCurrentUser: (user) => set({ currentUser: user }),
      selectNode: (nodeId) => set({ selectedNodeId: nodeId }),
      setEntropyResults: (results) => set({ entropyResults: results }),
      setMermaidCode: (code) => set({ mermaidCode: code }),
      
      // 创建任务
      createTask: async (mode, startDate, endDateParam) => {
        set({ isLoading: true, error: null });
        try {
          const { currentUser } = get();
          if (!currentUser) {
            throw new Error('用户未登录');
          }
          
          const response = await sessionApi.createSession({
            user_id: currentUser.id,
            user_role: currentUser.role === 'global_manager' ? 'manager' : 'business',
            mode,
            start_date: startDate,
            end_date: endDateParam,
            comparison_period: 'prev_month',
          });
          
          const treePreview = await treeApi.previewTree();
          
          const task: AttributionTask = {
            task_id: response.session_id,
            mode,
            state: convertBackendState(response.state),
            analysis_period: {
              start_date: startDate,
              end_date: endDateParam,
              comparison_period: 'prev_month',
            },
            indicator_tree: {
              version: '1.0.0',
              root: {
                id: 'gmv',
                name: 'GMV',
                type: 'operation',
                level: 0,
                level_code: 'L0',
                entropy_threshold: 0.2,
                children: [],
              },
            },
            current_node_id: 'gmv',
            attribution_chain: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          
          set({ 
            currentTask: task, 
            selectedNodeId: task.current_node_id,
            mermaidCode: treePreview.mermaid,
            drillDownHistory: [],
            lastEntropyResult: null,
            isLoading: false 
          });
        } catch (err) {
          set({ 
            error: err instanceof Error ? err.message : '创建任务失败', 
            isLoading: false 
          });
        }
      },
      
      // 继续任务（手动模式）
      continueTask: async () => {
        const { currentTask } = get();
        if (!currentTask) return;
        
        set({ isLoading: true, error: null });
        
        try {
          const response = await sessionApi.continueSession(currentTask.task_id);
          
          set({
            currentTask: {
              ...currentTask,
              state: convertBackendState(response.state),
              updated_at: new Date().toISOString(),
            },
            isLoading: false,
          });
        } catch (err) {
          set({ 
            error: err instanceof Error ? err.message : '继续任务失败', 
            isLoading: false 
          });
        }
      },
      
      // 提交结论
      submitConclusion: async (conclusion) => {
        const { currentTask } = get();
        if (!currentTask) return;
        
        set({ isLoading: true, error: null });
        
        try {
          await sessionApi.submitConclusion(currentTask.task_id, conclusion);
          
          const result = await sessionApi.getSessionResult(currentTask.task_id);
          
          set({
            currentTask: {
              ...currentTask,
              state: 'FINAL_REPORT',
              attribution_chain: result.attribution_chain.map(node => ({
                node_id: node.node_id,
                node_name: node.node_name,
                level_code: node.level_code,
                current_value: node.current_value,
                base_value: node.base_value,
                change_rate: node.change_rate,
                contribution_to_gmv: node.contribution_to_gmv,
                entropy_reduction: node.entropy_reduction,
                selected_dimension: node.selected_dimension,
              })),
              updated_at: new Date().toISOString(),
            },
            isLoading: false,
          });
        } catch (err) {
          set({ 
            error: err instanceof Error ? err.message : '提交结论失败', 
            isLoading: false 
          });
        }
      },
      
      // 刷新任务状态
      refreshTaskStatus: async () => {
        const { currentTask } = get();
        if (!currentTask) return;
        
        try {
          const status = await sessionApi.getSessionStatus(currentTask.task_id);
          
          set({
            currentTask: {
              ...currentTask,
              state: convertBackendState(status.state),
              mode: status.mode as AnalysisMode || currentTask.mode,
              updated_at: new Date().toISOString(),
            },
          });
        } catch (err) {
          console.error('刷新状态失败:', err);
        }
      },
      
      // 加载指标树预览
      loadTreePreview: async () => {
        try {
          const preview = await treeApi.previewTree();
          set({ mermaidCode: preview.mermaid });
        } catch (err) {
          console.error('加载指标树失败:', err);
        }
      },
      
      // 节点下钻分析
      drillDown: async (nodeId, nodeName, dimensionPool, rawData) => {
        set({ isAnalyzing: true, error: null, selectedNodeId: nodeId });
        
        try {
          const response = await algorithmApi.fullAttributionAnalysis({
            node_id: nodeId,
            dimension_pool: dimensionPool,
            raw_data: rawData,
            entropy_threshold: 0.2,
            cross_timeout: 3,
          });
          
          // 记录下钻历史
          const record: DrillDownRecord = {
            nodeId,
            nodeName,
            timestamp: new Date().toISOString(),
            entropyResults: response.single_dimension_results,
            selectedDimension: response.selected_dimension,
            selectedChild: response.selected_child,
            crossDimension: response.cross_dimension || null,
          };
          
          set((state) => ({
            drillDownHistory: [...state.drillDownHistory, record],
            lastEntropyResult: {
              results: response.single_dimension_results,
              selectedDimension: response.selected_dimension,
              selectedChild: response.selected_child,
              crossDimension: response.cross_dimension || null,
            },
            isAnalyzing: false,
          }));
          
          // 如果任务存在，更新当前节点
          const { currentTask } = get();
          if (currentTask) {
            set({
              currentTask: {
                ...currentTask,
                current_node_id: nodeId,
                updated_at: new Date().toISOString(),
              },
            });
          }
          
          // 如果交叉维度未完成，启动轮询
          if (response.cross_dimension && !response.cross_dimension.completed) {
            setTimeout(() => {
              get().refreshCrossDimension(nodeId);
            }, 5000);
          }
        } catch (err) {
          set({ 
            error: err instanceof Error ? err.message : '熵减计算失败', 
            isAnalyzing: false 
          });
        }
      },
      
      // 刷新交叉维度结果
      refreshCrossDimension: async (nodeId) => {
        const { lastEntropyResult, drillDownHistory } = get();
        if (!lastEntropyResult) return;
        
        try {
          const response = await algorithmApi.checkCrossDimension({
            node_id: nodeId,
            dimension_pool: [],
            raw_data: {},
            single_results: lastEntropyResult.results,
            entropy_threshold: 0.2,
            timeout_seconds: 3,
          });
          
          const newCross = response;
          
          set({
            lastEntropyResult: {
              ...lastEntropyResult,
              crossDimension: newCross,
            },
            drillDownHistory: drillDownHistory.map((record) =>
              record.nodeId === nodeId
                ? { ...record, crossDimension: newCross }
                : record
            ),
          });
          
          // 若仍未完成，继续轮询（最多3次）
          if (!newCross.completed) {
            const attempt = (lastEntropyResult.crossDimension?.pending?.length || 0);
            if (attempt < 3) {
              setTimeout(() => {
                get().refreshCrossDimension(nodeId);
              }, 5000);
            }
          }
        } catch (err) {
          console.error('刷新交叉维度失败:', err);
        }
      },
      
      // 高亮时间轴对应路径
      highlightStepPath: (stepIndex) => {
        const { drillDownHistory } = get();
        const path = ['gmv'];
        for (let i = 0; i <= stepIndex && i < drillDownHistory.length; i++) {
          const record = drillDownHistory[i];
          if (record.selectedChild) {
            path.push(record.selectedChild);
          }
        }
        set({ highlightedPath: path });
      },
      
      // 返回上一步
      goBack: () => {
        const { drillDownHistory } = get();
        if (drillDownHistory.length <= 1) {
          set({ 
            drillDownHistory: [], 
            lastEntropyResult: null,
            selectedNodeId: 'gmv',
            highlightedPath: ['gmv'],
          });
          return;
        }
        
        const newHistory = drillDownHistory.slice(0, -1);
        const previousRecord = newHistory[newHistory.length - 1];
        
        set({
          drillDownHistory: newHistory,
          lastEntropyResult: previousRecord ? {
            results: previousRecord.entropyResults,
            selectedDimension: previousRecord.selectedDimension,
            selectedChild: previousRecord.selectedChild,
            crossDimension: previousRecord.crossDimension,
          } : null,
          selectedNodeId: previousRecord?.nodeId || 'gmv',
          highlightedPath: ['gmv', ...(newHistory.map(h => h.selectedChild).filter(Boolean) as string[])],
        });
      },
      
      // 重置下钻
      resetDrillDown: () => {
        set({
          drillDownHistory: [],
          lastEntropyResult: null,
          selectedNodeId: 'gmv',
          highlightedPath: ['gmv'],
        });
      },
      
      // 权限检查
      canViewNode: (_nodeId, permissionScope) => {
        const { currentUser } = get();
        if (!currentUser) return false;
        
        if (currentUser.role === 'global_manager') return true;
        
        if (permissionScope && permissionScope.length > 0) {
          return permissionScope.some(scope => 
            currentUser.assigned_regions.includes(scope) ||
            currentUser.permissions.includes(scope)
          );
        }
        
        return true;
      },
      
      isGlobalManager: () => {
        const { currentUser } = get();
        return currentUser?.role === 'global_manager';
      },
    }),
    { name: 'SessionStore' }
  )
);

// 导出 API 供组件直接使用
export { sessionApi, algorithmApi, treeApi };
