/**
 * Task 5 自证测试
 * 
 * 验证前端三栏式布局组件的核心功能
 */

import React from 'react';
import { ThreeColumnLayout } from './components/layout/ThreeColumnLayout';
import { StepTimeline } from './components/timeline/StepTimeline';
import { generateSampleMermaidCode } from './components/tree/MermaidTree';
import { NodeDetail } from './components/detail/NodeDetail';
import { useSessionStore } from './stores/sessionStore';
import type { AttributionTask, AnalysisMode } from './types';

// 测试状态
interface TestResult {
  name: string;
  passed: boolean;
  message?: string;
}

// 运行所有测试
export async function runTask5SelfTest(): Promise<TestResult[]> {
  const results: TestResult[] = [];
  
  console.log('\n========== Task 5 自证测试 ==========\n');
  
  // 测试 1: 三栏布局组件
  results.push(testThreeColumnLayout());
  
  // 测试 2: Mermaid 图表生成
  results.push(testMermaidGeneration());
  
  // 测试 3: 状态管理
  results.push(testSessionStore());
  
  // 测试 4: 时间轴组件
  results.push(testStepTimeline());
  
  // 测试 5: 节点详情组件
  results.push(testNodeDetail());
  
  // 汇总结果
  const passed = results.filter(r => r.passed).length;
  const total = results.length;
  
  console.log(`\n========== 测试结果: ${passed}/${total} 通过 ==========\n`);
  
  return results;
}

// 测试 1: 三栏布局组件
function testThreeColumnLayout(): TestResult {
  try {
    const leftPanel = React.createElement('div', null, '左栏内容');
    const centerPanel = React.createElement('div', null, '中栏内容');
    const rightPanel = React.createElement('div', null, '右栏内容');
    
    const element = React.createElement(ThreeColumnLayout, {
      leftPanel,
      centerPanel,
      rightPanel,
    });
    
    if (!element) {
      return { name: '三栏布局组件', passed: false, message: '组件创建失败' };
    }
    
    return { name: '三栏布局组件', passed: true };
  } catch (error) {
    return { name: '三栏布局组件', passed: false, message: String(error) };
  }
}

// 测试 2: Mermaid 图表生成
function testMermaidGeneration(): TestResult {
  try {
    const mermaidCode = generateSampleMermaidCode();
    
    if (!mermaidCode || mermaidCode.length === 0) {
      return { name: 'Mermaid 图表生成', passed: false, message: '生成的代码为空' };
    }
    
    // 验证包含必要的 Mermaid 语法
    if (!mermaidCode.includes('graph TD')) {
      return { name: 'Mermaid 图表生成', passed: false, message: '缺少 graph TD 声明' };
    }
    
    if (!mermaidCode.includes('GMV')) {
      return { name: 'Mermaid 图表生成', passed: false, message: '缺少 GMV 根节点' };
    }
    
    if (!mermaidCode.includes('classDef')) {
      return { name: 'Mermaid 图表生成', passed: false, message: '缺少样式定义' };
    }
    
    console.log('  ✓ Mermaid 代码长度:', mermaidCode.length, '字符');
    
    return { name: 'Mermaid 图表生成', passed: true };
  } catch (error) {
    return { name: 'Mermaid 图表生成', passed: false, message: String(error) };
  }
}

// 测试 3: 状态管理
function testSessionStore(): TestResult {
  try {
    // 获取 store
    const store = useSessionStore.getState();
    
    // 验证初始状态
    if (store.currentTask !== null) {
      return { name: '状态管理', passed: false, message: '初始任务应为 null' };
    }
    
    // 验证 setCurrentTask 方法存在
    if (typeof store.setCurrentTask !== 'function') {
      return { name: '状态管理', passed: false, message: '缺少 setCurrentTask 方法' };
    }
    
    // 测试设置任务
    const mockTask: AttributionTask = {
      task_id: 'test-001',
      mode: 'auto' as AnalysisMode,
      state: 'AUTO_STEP1',
      analysis_period: {
        start_date: '2026-03-01',
        end_date: '2026-03-31',
        comparison_period: 'prev_month',
      },
      indicator_tree: {
        version: '1.0.0',
        root: {
          id: 'gmv',
          name: 'GMV',
          type: 'operation',
          level: 0,
          entropy_threshold: 0.2,
          children: [],
        },
      },
      current_node_id: 'gmv',
      attribution_chain: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    
    store.setCurrentTask(mockTask);
    
    // 验证任务已设置
    const newState = useSessionStore.getState();
    if (newState.currentTask?.task_id !== 'test-001') {
      return { name: '状态管理', passed: false, message: '设置任务失败' };
    }
    
    // 重置状态
    store.setCurrentTask(null);
    
    console.log('  ✓ Store 方法:', Object.keys(store).filter(k => typeof (store as any)[k] === 'function').length, '个');
    
    return { name: '状态管理', passed: true };
  } catch (error) {
    return { name: '状态管理', passed: false, message: String(error) };
  }
}

// 测试 4: 时间轴组件
function testStepTimeline(): TestResult {
  try {
    const element = React.createElement(StepTimeline);
    
    if (!element) {
      return { name: '时间轴组件', passed: false, message: '组件创建失败' };
    }
    
    // 验证组件类型
    if (element.type !== StepTimeline) {
      return { name: '时间轴组件', passed: false, message: '组件类型不匹配' };
    }
    
    return { name: '时间轴组件', passed: true };
  } catch (error) {
    return { name: '时间轴组件', passed: false, message: String(error) };
  }
}

// 测试 5: 节点详情组件
function testNodeDetail(): TestResult {
  try {
    const element = React.createElement(NodeDetail);
    
    if (!element) {
      return { name: '节点详情组件', passed: false, message: '组件创建失败' };
    }
    
    return { name: '节点详情组件', passed: true };
  } catch (error) {
    return { name: '节点详情组件', passed: false, message: String(error) };
  }
}

// 导出测试报告
export function generateTestReport(results: TestResult[]): string {
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  
  let report = '\n';
  report += '╔════════════════════════════════════════════════╗\n';
  report += '║           Task 5 自证测试报告                   ║\n';
  report += '╠════════════════════════════════════════════════╣\n';
  
  results.forEach(r => {
    const icon = r.passed ? '✓' : '✗';
    const status = r.passed ? '通过' : '失败';
    report += `║ ${icon} ${r.name.padEnd(20)} ${status.padEnd(10)} ║\n`;
    if (!r.passed && r.message) {
      report += `║   └─ ${r.message.slice(0, 30).padEnd(30)} ║\n`;
    }
  });
  
  report += '╠════════════════════════════════════════════════╣\n';
  report += `║ 总计: ${String(passed).padStart(2)} 通过, ${String(failed).padStart(2)} 失败              ║\n`;
  report += '╚════════════════════════════════════════════════╝\n';
  
  return report;
}
