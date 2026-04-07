/// <reference types="vite/client" />
import axios from 'axios';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============ 类型定义 ============

export interface CreateSessionRequest {
  user_id: string;
  user_role: string;
  mode: 'auto' | 'manual';
  start_date: string;
  end_date: string;
  comparison_period?: string;
  indicator_tree_config?: Record<string, unknown>;
}

export interface CreateSessionResponse {
  session_id: string;
  state: string;
  mode: string;
  message: string;
}

export interface SessionStatusResponse {
  session_id: string;
  state: string;
  mode: string | null;
  step: number | null;
  can_export_process: boolean;
  can_export_full: boolean;
  is_terminal: boolean;
}

export interface SessionResultResponse {
  session_id: string;
  state: string;
  attribution_chain: AttributionNodeResult[];
  conclusion: BusinessConclusion | null;
  can_export: boolean;
}

export interface AttributionNodeResult {
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

export interface BusinessConclusion {
  reason_type: string;
  detailed_explanation: string;
  involved_departments: string[];
  suggested_actions: string;
  confidence_level: 'high' | 'medium' | 'low';
}

export interface SubmitConclusionRequest {
  session_id: string;
  reason_type: string;
  detailed_explanation: string;
  involved_departments: string[];
  suggested_actions: string;
  confidence_level: 'high' | 'medium' | 'low';
}

// 熵减计算相关类型
export interface EntropyCalculateRequest {
  node_id: string;
  dimension_pool: Array<{
    dimension_name: string;
    dimension_id: string;
    child_nodes: string[];
    data_slice_rule?: Record<string, unknown>;
  }>;
  raw_data: Record<string, number>;
  entropy_threshold?: number;
}

export interface EntropyCalculateResponse {
  node_id: string;
  entropy_threshold: number;
  selected_dimension: string | null;
  selected_child: string | null;
  should_drill_down: boolean;
  single_dimension_results: SingleDimensionResult[];
  summary: string;
}

export interface SingleDimensionResult {
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

export interface ChildDetail {
  child_name: string;
  signed_contribution: number;
  abs_contribution: number;
  share: number;
}

// 交叉维度相关类型
export interface CrossDimensionRequest {
  node_id: string;
  dimension_pool: Array<{
    dimension_name: string;
    dimension_id: string;
    child_nodes: string[];
  }>;
  raw_data: Record<string, number>;
  single_results: SingleDimensionResult[];
  entropy_threshold?: number;
  timeout_seconds?: number;
}

export interface CrossDimensionResponse {
  completed: boolean;
  results: CrossDimensionResult[];
  pending: Array<[string, string]>;
  recommendations: CrossDimensionRecommendation[];
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

// 贡献度计算相关类型
export interface ContributionRequest {
  indicator_type: 'additive' | 'multiplicative' | 'pseudo_weight';
  data: {
    current_values: Record<string, number>;
    base_values: Record<string, number>;
    weights?: Record<string, number>;
    gmv_decline?: number;
  };
}

export interface ContributionResponse {
  indicator_type: string;
  contributions: Record<string, {
    contribution_to_parent: number;
    contribution_to_gmv: number;
    decline_rate: number;
  }>;
}

// 指标树相关类型
export interface TreePreviewResponse {
  valid: boolean;
  errors: string[];
  mermaid: string;
}

export interface TreeValidateResponse {
  valid: boolean;
  errors: string[];
}

// ============ Session API ============

export const sessionApi = {
  /**
   * 创建新的归因分析会话
   */
  async createSession(request: CreateSessionRequest): Promise<CreateSessionResponse> {
    const response = await api.post<CreateSessionResponse>('/sessions/create', request);
    return response.data;
  },

  /**
   * 获取会话状态
   */
  async getSessionStatus(sessionId: string): Promise<SessionStatusResponse> {
    const response = await api.get<SessionStatusResponse>(`/sessions/${sessionId}/status`);
    return response.data;
  },

  /**
   * 继续手动模式的下一步
   */
  async continueSession(sessionId: string): Promise<{ success: boolean; state: string; message: string }> {
    const response = await api.post<{ success: boolean; state: string; message: string }>(`/sessions/${sessionId}/continue`);
    return response.data;
  },

  /**
   * 提交业务结论
   */
  async submitConclusion(sessionId: string, conclusion: Omit<SubmitConclusionRequest, 'session_id'>): Promise<{ success: boolean; state: string }> {
    const response = await api.post<{ success: boolean; state: string }>(`/sessions/${sessionId}/submit-conclusion`, {
      session_id: sessionId,
      ...conclusion,
    });
    return response.data;
  },

  /**
   * 获取会话完整结果
   */
  async getSessionResult(sessionId: string): Promise<SessionResultResponse> {
    const response = await api.get<SessionResultResponse>(`/sessions/${sessionId}/result`);
    return response.data;
  },
};

// ============ Algorithm API ============

export const algorithmApi = {
  /**
   * 计算单维度熵减
   */
  async calculateEntropy(request: EntropyCalculateRequest): Promise<EntropyCalculateResponse> {
    const response = await api.post<EntropyCalculateResponse>('/entropy/calculate', request);
    return response.data;
  },

  /**
   * 执行交叉维度校验
   */
  async checkCrossDimension(request: CrossDimensionRequest): Promise<CrossDimensionResponse> {
    const response = await api.post<CrossDimensionResponse>('/entropy/cross-dimension', request);
    return response.data;
  },

  /**
   * 执行完整归因分析（熵减 + 交叉维度）
   */
  async fullAttributionAnalysis(request: EntropyCalculateRequest & { cross_timeout?: number }): Promise<EntropyCalculateResponse & { cross_dimension: CrossDimensionResponse }> {
    const response = await api.post<EntropyCalculateResponse & { cross_dimension: CrossDimensionResponse }>('/entropy/analyze', request);
    return response.data;
  },

  /**
   * 计算贡献度
   */
  async calculateContribution(request: ContributionRequest): Promise<ContributionResponse> {
    const response = await api.post<ContributionResponse>('/entropy/contribution', request);
    return response.data;
  },

  /**
   * 获取 PRD 4.1 节示例数据
   */
  async getDemoData(): Promise<{
    scenario: string;
    raw_data: Record<string, number>;
    dimension_pool: Array<{
      dimension_name: string;
      dimension_id: string;
      child_nodes: string[];
    }>;
    expected_results: Record<string, unknown>;
  }> {
    const response = await api.get('/entropy/demo/prd-4-1');
    return response.data;
  },
};

// ============ Indicator Tree API ============

export const treeApi = {
  /**
   * 预览指标树（返回 Mermaid 语法）
   */
  async previewTree(configPath?: string): Promise<TreePreviewResponse> {
    const params = configPath ? { config_path: configPath } : {};
    const response = await api.get<TreePreviewResponse>('/tree/preview', { params });
    return response.data;
  },

  /**
   * 校验指标树配置
   */
  async validateTree(configPath?: string): Promise<TreeValidateResponse> {
    const params = configPath ? { config_path: configPath } : {};
    const response = await api.get<TreeValidateResponse>('/tree/validate', { params });
    return response.data;
  },
};

// ============ Export API ============

export const exportApi = {
  /**
   * 导出 Word 报告
   */
  async exportWord(sessionId: string, reportType: 'process' | 'full'): Promise<Blob> {
    const response = await api.get(`/export/${sessionId}/word`, {
      params: { report_type: reportType },
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * 导出 PDF 报告
   */
  async exportPDF(sessionId: string, reportType: 'process' | 'full'): Promise<Blob> {
    const response = await api.get(`/export/${sessionId}/pdf`, {
      params: { report_type: reportType },
      responseType: 'blob',
    });
    return response.data;
  },
};

// ============ Upload API ============

export interface UploadFileResponse {
  success: boolean;
  file_id: string;
  original_name: string;
  file_type: string;
  file_size: number;
  parse_status: 'pending' | 'success' | 'error';
}

export interface UploadedFileItem {
  file_id: string;
  original_name: string;
  file_type: string;
  file_size: number;
  parse_status: 'pending' | 'success' | 'error';
}

export const uploadApi = {
  /**
   * 上传文件
   */
  async upload(sessionId: string, file: File): Promise<UploadFileResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadFileResponse>(`/upload/${sessionId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * 获取已上传文件列表
   */
  async listFiles(sessionId: string): Promise<{ session_id: string; files: UploadedFileItem[] }> {
    const response = await api.get<{ session_id: string; files: UploadedFileItem[] }>(`/upload/${sessionId}/files`);
    return response.data;
  },

  /**
   * 删除文件
   */
  async deleteFile(sessionId: string, fileId: string): Promise<{ success: boolean; file_id: string }> {
    const response = await api.delete<{ success: boolean; file_id: string }>(`/upload/${sessionId}/${fileId}`);
    return response.data;
  },
};

// ============ Health Check ============

export const healthApi = {
  /**
   * 健康检查
   */
  async checkHealth(): Promise<{ status: string }> {
    const response = await api.get<{ status: string }>('/health');
    return response.data;
  },
};

export default api;
