// 指标树相关类型

export type NodeType = 'organization' | 'operation' | 'action';

export interface DataSource {
  db_view: string;
  field: string;
  filter?: string;
  agg_func: 'SUM' | 'AVG' | 'COUNT' | 'MAX' | 'MIN';
  group_by?: string[];
}

export interface ChildMapping {
  node_id: string;
  group_value: string;
}

export interface DataSliceRule {
  source_view: string;
  group_by_field: string;
  metric_field: string;
  agg_func: 'SUM' | 'AVG' | 'COUNT' | 'MAX' | 'MIN';
  filter_template?: string;
  child_mapping?: ChildMapping[];
}

export interface Dimension {
  dimension_name: string;
  dimension_id: string;
  child_nodes: string[];
  data_slice_rule?: DataSliceRule;
}

export interface TreeNode {
  id: string;
  name: string;
  type: NodeType;
  level: number;
  level_code?: string;
  parent_id?: string;
  formula?: string;
  pseudo_weight?: number;
  weight?: number;
  entropy_threshold: number;
  data_source?: DataSource;
  permission_scope?: string[];
  children: TreeNode[];
  dimension_pool?: Dimension[];
}

export interface IndicatorTree {
  version: string;
  root: TreeNode;
}

// 归因任务相关类型

export type AnalysisMode = 'auto' | 'manual';

export type TaskState = 
  | 'INIT'
  | 'MODE_SELECT'
  | 'AUTO_STEP1' | 'AUTO_STEP2' | 'AUTO_STEP3' | 'AUTO_STEP4' | 'AUTO_SUMMARY'
  | 'MANUAL_STEP1' | 'MANUAL_STEP2' | 'MANUAL_STEP3' | 'MANUAL_STEP4'
  | 'LLM_EXPLAIN_1' | 'LLM_EXPLAIN_2' | 'LLM_EXPLAIN_3' | 'LLM_EXPLAIN_4'
  | 'LLM_NARRATIVE'
  | 'HUMAN_INPUT'
  | 'FINAL_REPORT'
  | 'ALGO_ERROR'
  | 'DATA_MISSING';

export interface AnalysisPeriod {
  start_date: string;
  end_date: string;
  comparison_period: 'prev_month' | 'prev_quarter' | 'prev_year' | string;
}

export interface AttributionTask {
  task_id: string;
  mode: AnalysisMode;
  state: TaskState;
  analysis_period: AnalysisPeriod;
  indicator_tree: IndicatorTree;
  current_node_id: string;
  attribution_chain: AttributionNode[];
  created_at: string;
  updated_at: string;
}

export interface AttributionNode {
  node_id: string;
  node_name: string;
  level_code: string;
  current_value: number;
  base_value: number;
  change_rate: number;
  contribution_to_gmv: number;
  entropy_reduction?: number;
  selected_dimension?: string;
}

// 熵减计算结果

export interface ChildDetail {
  child_name: string;
  signed_contribution: number;
  abs_contribution: number;
  share: number;
}

export interface EntropyResult {
  dimension: string;
  num_categories: number;
  entropy: number;
  max_entropy: number;
  entropy_reduction: number;
  entropy_reduction_normalized: number;
  is_key_dimension: boolean;
  top_child: string;
  top_child_share: number;
  child_details: ChildDetail[];
}

export interface CrossDimensionResult {
  dimension_pair: [string, string];
  entropy_reduction: number;
  is_significant: boolean;
  top_combination: string;
  top_combination_share: number;
}

export interface CrossDimensionRecommendation {
  dimension_pair: [string, string];
  entropy_reduction: number;
  reason: string;
}

export interface CrossDimensionResponse {
  completed: boolean;
  results: CrossDimensionResult[];
  pending: Array<[string, string]>;
  recommendations: CrossDimensionRecommendation[];
}

export interface EntropyCalculationResponse {
  task_id: string;
  parent_node_id: string;
  entropy_results: EntropyResult[];
  selected_dimension: string;
  selected_child: string;
  contribution_results: Record<string, {
    contribution_to_parent: number;
    contribution_to_gmv: number;
    decline_rate: number;
  }>;
  cross_dimension?: CrossDimensionResponse;
}

// 用户角色

export type UserRole = 'global_manager' | 'regional_manager' | 'business_user';

export interface User {
  id: string;
  name: string;
  role: UserRole;
  assigned_regions: string[];
  permissions: string[];
}

// 业务结论

export interface BusinessConclusion {
  reason_types: ('external_policy' | 'organization' | 'competitor' | 'seasonal' | 'data_error' | 'other')[];
  detail_description: string;
  involved_departments?: string;
  suggested_actions?: string;
  confidence_level: 'high' | 'medium' | 'low';
  attached_files?: string[];
}
