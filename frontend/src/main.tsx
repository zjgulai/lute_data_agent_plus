/// <reference types="vite/client" />
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { ErrorBoundary } from './components/common/ErrorBoundary.tsx'

// 开发模式下运行自证测试
if (import.meta.env.DEV) {
  // Task 5 自证测试
  import('./Task5SelfTest').then(({ runTask5SelfTest, generateTestReport }) => {
    runTask5SelfTest().then(results => {
      console.log(generateTestReport(results));
    });
  });
  
  // Task 6 权限自证测试
  import('./components/debug/PermissionSelfTest').then(({ runPermissionSelfTest, generatePermissionTestReport }) => {
    const result = runPermissionSelfTest();
    console.log(generatePermissionTestReport(result));
  });
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
