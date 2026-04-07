import React, { useState } from 'react';
import { sessionApi, algorithmApi, treeApi, healthApi } from '../../services/api';
import type { EntropyCalculateRequest } from '../../services/api';

/**
 * API 测试组件
 * 
 * 用于开发和调试阶段测试后端 API 连通性
 */
export const ApiTester: React.FC = () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [results, setResults] = useState<Array<{ name: string; status: 'pending' | 'success' | 'error'; result?: any; error?: string }>>([]);
  const [isRunning, setIsRunning] = useState(false);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const addResult = (name: string, status: 'pending' | 'success' | 'error', result?: any, error?: string) => {
    setResults(prev => [...prev, { name, status, result, error }]);
  };

  const runTests = async () => {
    setResults([]);
    setIsRunning(true);

    // Test 1: Health Check
    try {
      addResult('Health Check', 'pending');
      const health = await healthApi.checkHealth();
      addResult('Health Check', 'success', health);
    } catch (err) {
      addResult('Health Check', 'error', undefined, err instanceof Error ? err.message : 'Unknown error');
    }

    // Test 2: Tree Preview
    try {
      addResult('Tree Preview', 'pending');
      const preview = await treeApi.previewTree();
      addResult('Tree Preview', 'success', { valid: preview.valid, errors: preview.errors, mermaidLength: preview.mermaid.length });
    } catch (err) {
      addResult('Tree Preview', 'error', undefined, err instanceof Error ? err.message : 'Unknown error');
    }

    // Test 3: Entropy Calculate
    try {
      addResult('Entropy Calculate', 'pending');
      const entropyRequest: EntropyCalculateRequest = {
        node_id: 'gmv',
        dimension_pool: [
          { dimension_name: '区域', dimension_id: 'region', child_nodes: ['美国', '中国', '欧洲', '亚太'] },
          { dimension_name: '产品', dimension_id: 'product', child_nodes: ['产品A', '产品B', '产品C'] },
        ],
        raw_data: {
          '美国': -1980000,
          '中国': 100000,
          '欧洲': -120000,
          '亚太': 0,
          '产品A': -1200000,
          '产品B': -800000,
          '产品C': 10000,
        },
        entropy_threshold: 0.2,
      };
      const entropy = await algorithmApi.calculateEntropy(entropyRequest);
      addResult('Entropy Calculate', 'success', {
        selected_dimension: entropy.selected_dimension,
        selected_child: entropy.selected_child,
        should_drill_down: entropy.should_drill_down,
        results_count: entropy.single_dimension_results.length,
      });
    } catch (err) {
      addResult('Entropy Calculate', 'error', undefined, err instanceof Error ? err.message : 'Unknown error');
    }

    // Test 4: Create Session
    let sessionId = '';
    try {
      addResult('Create Session', 'pending');
      const session = await sessionApi.createSession({
        user_id: 'test-user',
        user_role: 'manager',
        mode: 'manual',
        start_date: '2026-02-01',
        end_date: '2026-02-28',
        comparison_period: 'prev_month',
      });
      sessionId = session.session_id;
      addResult('Create Session', 'success', { session_id: session.session_id, state: session.state });
    } catch (err) {
      addResult('Create Session', 'error', undefined, err instanceof Error ? err.message : 'Unknown error');
    }

    // Test 5: Get Session Status
    if (sessionId) {
      try {
        addResult('Get Session Status', 'pending');
        const status = await sessionApi.getSessionStatus(sessionId);
        addResult('Get Session Status', 'success', status);
      } catch (err) {
        addResult('Get Session Status', 'error', undefined, err instanceof Error ? err.message : 'Unknown error');
      }
    }

    setIsRunning(false);
  };

  const clearResults = () => {
    setResults([]);
  };

  return (
    <div className="p-4 space-y-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">API 连通性测试</h3>
        <div className="flex gap-2">
          <button
            onClick={clearResults}
            disabled={isRunning}
            className="px-3 py-1.5 text-xs bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50"
          >
            清除
          </button>
          <button
            onClick={runTests}
            disabled={isRunning}
            className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
          >
            {isRunning && (
              <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
            {isRunning ? '测试中...' : '运行测试'}
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="space-y-2">
          {results.map((result, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg text-xs ${
                result.status === 'pending'
                  ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                  : result.status === 'success'
                  ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                  : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'
              }`}
            >
              <div className="flex items-center gap-2">
                {result.status === 'pending' && (
                  <svg className="animate-spin h-4 w-4 text-yellow-500" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                )}
                {result.status === 'success' && (
                  <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {result.status === 'error' && (
                  <svg className="h-4 w-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
                <span className={`font-medium ${
                  result.status === 'success' ? 'text-green-700 dark:text-green-400' :
                  result.status === 'error' ? 'text-red-700 dark:text-red-400' :
                  'text-yellow-700 dark:text-yellow-400'
                }`}>
                  {result.name}
                </span>
              </div>
              {result.result && (
                <pre className="mt-2 p-2 bg-white dark:bg-gray-800 rounded overflow-auto max-h-32">
                  {JSON.stringify(result.result, null, 2)}
                </pre>
              )}
              {result.error && (
                <p className="mt-1 text-red-600 dark:text-red-400">{result.error}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && !isRunning && (
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center py-4">
          点击"运行测试"检查 API 连通性
        </p>
      )}
    </div>
  );
};

export default ApiTester;
