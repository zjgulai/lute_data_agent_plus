/**
 * Task 6 权限自适应机制 - 自证测试
 * 
 * 验证权限过滤逻辑的正确性
 */

import type { TreeNode, User, UserRole } from '../../types';
import { filterTreeByPermission, shouldShowOrganizationTree } from '../../utils/permission';

// 测试用例类型
interface TestCase {
  name: string;
  user: User;
  input: {
    tree: TreeNode;
    targetNodeId?: string;
  };
  expected: {
    visibleNodeIds: string[];
    canViewOrganization: boolean;
  };
}

// 模拟指标树
const mockTree: TreeNode = {
  id: 'gmv',
  name: 'GMV',
  type: 'operation',
  level: 0,
  entropy_threshold: 0.2,
  children: [
    {
      id: 'org_side',
      name: '组织侧',
      type: 'organization',
      level: 1,
      entropy_threshold: 0.2,
      children: [
        {
          id: 'org_asia_pacific',
          name: '亚太区',
          type: 'organization',
          level: 2,
          entropy_threshold: 0.2,
          children: [
            {
              id: 'org_sg',
              name: '新加坡',
              type: 'organization',
              level: 3,
              entropy_threshold: 0.2,
              children: [
                {
                  id: 'org_sg_marketing',
                  name: '新加坡市场部',
                  type: 'organization',
                  level: 4,
                  entropy_threshold: 0.2,
                  permission_scope: ['sg_marketing_manager', 'global_manager'],
                  children: [],
                },
              ],
            },
          ],
        },
      ],
    },
    {
      id: 'op_side',
      name: '经营侧',
      type: 'operation',
      level: 1,
      entropy_threshold: 0.2,
      children: [
        {
          id: 'op_user',
          name: '用户',
          type: 'operation',
          level: 2,
          entropy_threshold: 0.2,
          children: [],
        },
        {
          id: 'op_product',
          name: '产品',
          type: 'operation',
          level: 2,
          entropy_threshold: 0.2,
          children: [],
        },
      ],
    },
  ],
};

// 测试用例
const testCases: TestCase[] = [
  {
    name: '全局管理者 - 查看完整树',
    user: {
      id: 'user-001',
      name: '张总',
      role: 'global_manager' as UserRole,
      assigned_regions: ['global'],
      permissions: ['view_all'],
    },
    input: { tree: mockTree },
    expected: {
      visibleNodeIds: ['gmv', 'org_side', 'org_asia_pacific', 'org_sg', 'org_sg_marketing', 'op_side', 'op_user', 'op_product'],
      canViewOrganization: true,
    },
  },
  {
    name: '区域管理者 - 仅看所辖区域',
    user: {
      id: 'user-002',
      name: '李经理',
      role: 'regional_manager' as UserRole,
      assigned_regions: ['asia_pacific'],
      permissions: ['view_regional'],
    },
    input: { tree: mockTree },
    expected: {
      visibleNodeIds: ['gmv', 'org_side', 'org_asia_pacific'], // 只看亚太区及以上
      canViewOrganization: true,
    },
  },
  {
    name: '业务用户 - 仅看经营侧',
    user: {
      id: 'user-003',
      name: '王运营',
      role: 'business_user' as UserRole,
      assigned_regions: [],
      permissions: ['view_operation'],
    },
    input: { tree: mockTree },
    expected: {
      visibleNodeIds: ['gmv', 'op_side', 'op_user', 'op_product'], // 不看组织侧
      canViewOrganization: false,
    },
  },
  {
    name: '新加坡市场部 - 仅看指定节点',
    user: {
      id: 'user-004',
      name: '陈市场',
      role: 'business_user' as UserRole,
      assigned_regions: [],
      permissions: ['sg_marketing_manager'],
    },
    input: { tree: mockTree },
    expected: {
      visibleNodeIds: ['gmv', 'org_side', 'org_asia_pacific', 'org_sg', 'org_sg_marketing'],
      canViewOrganization: true,
    },
  },
];

// 运行自证测试
export function runPermissionSelfTest(): {
  passed: number;
  failed: number;
  results: Array<{
    name: string;
    passed: boolean;
    error?: string;
    details?: {
      expected: string[];
      actual: string[];
      missing: string[];
      extra: string[];
    };
  }>;
} {
  console.log('\n========== Task 6 权限自适应机制自证测试 ==========\n');
  
  const results: Array<{
    name: string;
    passed: boolean;
    error?: string;
    details?: {
      expected: string[];
      actual: string[];
      missing: string[];
      extra: string[];
    };
  }> = [];
  
  for (const testCase of testCases) {
    try {
      // 测试组织树可见性
      const canViewOrganization = shouldShowOrganizationTree(testCase.user);
      
      if (canViewOrganization !== testCase.expected.canViewOrganization) {
        results.push({
          name: testCase.name,
          passed: false,
          error: `组织树可见性错误: 期望 ${testCase.expected.canViewOrganization}, 实际 ${canViewOrganization}`,
        });
        continue;
      }
      
      // 测试节点过滤
      const filteredTree = filterTreeByPermission(mockTree, testCase.user);
      const visibleNodeIds = collectNodeIds(filteredTree);
      
      // 比较结果
      const expected = testCase.expected.visibleNodeIds.sort();
      const actual = visibleNodeIds.sort();
      const missing = expected.filter(id => !actual.includes(id));
      const extra = actual.filter(id => !expected.includes(id));
      
      const passed = missing.length === 0 && extra.length === 0;
      
      results.push({
        name: testCase.name,
        passed,
        ...(passed ? {} : {
          details: {
            expected,
            actual,
            missing,
            extra,
          },
        }),
      });
      
      if (passed) {
        console.log(`✓ ${testCase.name}`);
      } else {
        console.log(`✗ ${testCase.name}`);
        console.log(`  缺失节点: [${missing.join(', ')}]`);
        console.log(`  多余节点: [${extra.join(', ')}]`);
      }
    } catch (error) {
      results.push({
        name: testCase.name,
        passed: false,
        error: String(error),
      });
      console.log(`✗ ${testCase.name} - 异常: ${error}`);
    }
  }
  
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  
  console.log(`\n========== 测试结果: ${passed}/${results.length} 通过 ==========\n`);
  
  return { passed, failed, results };
}

// 收集树中所有节点ID
function collectNodeIds(node: TreeNode | null): string[] {
  if (!node) return [];
  
  const ids = [node.id];
  if (node.children) {
    for (const child of node.children) {
      ids.push(...collectNodeIds(child));
    }
  }
  return ids;
}

// 生成测试报告
export function generatePermissionTestReport(result: ReturnType<typeof runPermissionSelfTest>): string {
  let report = '\n';
  report += '╔════════════════════════════════════════════════════════╗\n';
  report += '║         Task 6 权限自适应机制自证测试报告               ║\n';
  report += '╠════════════════════════════════════════════════════════╣\n';
  
  for (const r of result.results) {
    const icon = r.passed ? '✓' : '✗';
    const status = r.passed ? '通过' : '失败';
    report += `║ ${icon} ${r.name.slice(0, 40).padEnd(40)} ${status.padEnd(6)} ║\n`;
    
    if (!r.passed && r.details) {
      if (r.details.missing.length > 0) {
        report += `║   缺失: ${r.details.missing.join(', ').slice(0, 40).padEnd(40)} ║\n`;
      }
      if (r.details.extra.length > 0) {
        report += `║   多余: ${r.details.extra.join(', ').slice(0, 40).padEnd(40)} ║\n`;
      }
    }
    
    if (r.error) {
      report += `║   错误: ${r.error.slice(0, 40).padEnd(40)} ║\n`;
    }
  }
  
  report += '╠════════════════════════════════════════════════════════╣\n';
  report += `║ 总计: ${String(result.passed).padStart(2)} 通过, ${String(result.failed).padStart(2)} 失败                            ║\n`;
  report += '╚════════════════════════════════════════════════════════╝\n';
  
  return report;
}

export default runPermissionSelfTest;
