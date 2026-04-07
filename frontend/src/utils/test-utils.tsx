import type { ReactElement } from 'react';

/**
 * 测试工具函数
 * 
 * 提供前端测试辅助功能
 */

// 简单的 render 函数（不依赖 @testing-library/react）
export function render(_ui: ReactElement): { container: HTMLDivElement } {
  const container = document.createElement('div');
  container.id = 'test-root';
  document.body.appendChild(container);
  
  // 注意：这里只是一个简单的占位实现
  // 实际测试应使用 ReactDOM.render 或 React 18 的 createRoot
  
  return { container };
}

// 清理函数
export function cleanup(): void {
  const testRoot = document.getElementById('test-root');
  if (testRoot) {
    document.body.removeChild(testRoot);
  }
}
