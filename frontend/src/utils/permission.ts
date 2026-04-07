/**
 * 权限控制工具函数
 * 
 * 实现 Task 6 权限自适应机制
 */

import type { TreeNode, User, UserRole, NodeType } from '../types';

/**
 * 判断用户是否可以看到组织侧指标树
 */
export function shouldShowOrganizationTree(user: User | null): boolean {
  if (!user) return false;
  
  // 全局管理者可以看完整双组织树
  if (user.role === 'global_manager') return true;
  
  // 区域管理者可以看组织侧
  if (user.role === 'regional_manager') return true;
  
  // 业务用户默认不看组织侧，除非有特殊权限
  if (user.role === 'business_user') {
    // 检查是否有组织侧相关权限
    return user.permissions.some(p => 
      p.includes('org_') || 
      p.includes('manager') ||
      p.includes('view_organization')
    );
  }
  
  return false;
}

/**
 * 判断用户是否可以查看特定节点
 */
export function canViewNode(node: TreeNode, user: User | null): boolean {
  if (!user) return false;
  
  // 全局管理者可以查看所有节点
  if (user.role === 'global_manager') return true;
  
  // 检查节点的 permission_scope
  if (node.permission_scope && node.permission_scope.length > 0) {
    // 节点有权限限制，检查用户是否匹配
    const hasPermission = node.permission_scope.some(scope =>
      user.permissions.includes(scope) ||
      user.assigned_regions.includes(scope)
    );
    
    // 如果用户有任意一个权限，则可以查看
    if (hasPermission) return true;
    
    // 如果节点有权限限制但用户没有匹配权限，则拒绝
    // 但允许查看父节点（用于导航）
    return false;
  }
  
  // 节点没有权限限制，根据类型判断
  if (node.type === 'organization') {
    return shouldShowOrganizationTree(user);
  }
  
  // 经营侧节点默认可见
  return true;
}

/**
 * 根据用户权限过滤指标树
 */
export function filterTreeByPermission(tree: TreeNode, user: User | null): TreeNode | null {
  if (!user) return null;
  
  // 递归过滤函数
  function filterNode(node: TreeNode): TreeNode | null {
    // 检查当前节点是否可见
    const canView = canViewNode(node, user);
    
    // 如果是组织侧根节点且用户无权查看，返回 null
    if (node.type === 'organization' && !shouldShowOrganizationTree(user)) {
      return null;
    }
    
    // 过滤子节点
    let filteredChildren: TreeNode[] = [];
    if (node.children && node.children.length > 0) {
      filteredChildren = node.children
        .map(child => filterNode(child))
        .filter((child): child is TreeNode => child !== null);
    }
    
    // 如果当前节点有权限限制且用户没有权限，但子节点有权限
    // 则只显示有权限的子节点
    if (!canView && filteredChildren.length === 0) {
      return null;
    }
    
    // 区域管理者：只能看到所辖区域
    if (user!.role === 'regional_manager' && node.type === 'organization') {
      // 检查节点是否与用户区域匹配
      const isInRegion = checkRegionMatch(node.id, user!.assigned_regions);
      if (!isInRegion && node.level > 0) {
        // 非当前区域且不是根节点，过滤掉子节点
        return {
          ...node,
          children: [],
        };
      }
    }
    
    // 返回过滤后的节点
    return {
      ...node,
      children: filteredChildren,
    };
  }
  
  return filterNode(tree);
}

/**
 * 检查节点区域是否匹配用户区域
 */
function checkRegionMatch(nodeId: string, assignedRegions: string[]): boolean {
  if (assignedRegions.includes('global')) return true;
  
  // 区域匹配规则
  const regionMappings: Record<string, string[]> = {
    'asia_pacific': ['org_asia_pacific', 'org_sg', 'org_cn', 'org_jp'],
    'singapore': ['org_sg', 'org_sg_marketing'],
    'china': ['org_cn'],
    'americas': ['org_us', 'org_ca'],
    'europe': ['org_eu', 'org_uk', 'org_de'],
  };
  
  for (const region of assignedRegions) {
    const matchingIds = regionMappings[region] || [region];
    if (matchingIds.some(id => nodeId.includes(id) || id.includes(nodeId))) {
      return true;
    }
  }
  
  return false;
}

/**
 * 获取用户角色显示名称
 */
export function getRoleDisplayName(role: UserRole): string {
  const roleNames: Record<UserRole, string> = {
    'global_manager': '全局管理者',
    'regional_manager': '区域管理者',
    'business_user': '业务用户',
  };
  return roleNames[role] || role;
}

/**
 * 获取用户可查看的节点类型
 */
export function getViewableNodeTypes(user: User | null): NodeType[] {
  if (!user) return [];
  
  const types: NodeType[] = ['operation', 'action'];
  
  if (shouldShowOrganizationTree(user)) {
    types.push('organization');
  }
  
  return types;
}

/**
 * 检查用户是否有导出权限
 */
export function canExportReports(user: User | null): boolean {
  if (!user) return false;
  
  if (user.role === 'global_manager') return true;
  
  return user.permissions.includes('export_reports');
}

/**
 * 检查用户是否可以提交结论
 */
export function canSubmitConclusion(user: User | null): boolean {
  if (!user) return false;
  
  if (user.role === 'global_manager') return true;
  if (user.role === 'regional_manager') return true;
  
  return user.permissions.includes('submit_conclusions');
}

/**
 * 根据权限生成 Mermaid 代码
 * 
 * 过滤掉用户无权查看的节点
 */
export function generatePermissionFilteredMermaid(
  tree: TreeNode,
  user: User | null,
  options?: {
    selectedNodeId?: string | null;
    highlightPath?: string[];
  }
): string {
  if (!user) return '';
  
  const filteredTree = filterTreeByPermission(tree, user);
  if (!filteredTree) return '';
  
  const lines: string[] = ['graph TD'];
  const styles: string[] = [];
  
  function processNode(node: TreeNode, parentId?: string) {
    const nodeId = node.id.replace(/[^a-zA-Z0-9]/g, '_');
    // 节点显示名称（可根据需要自定义）
    void `${node.level_code}: ${node.name}`;
    
    // 节点样式类
    if (node.type === 'organization') {
      styles.push(`class ${nodeId} orgNode`);
    } else if (node.type === 'operation') {
      styles.push(`class ${nodeId} opNode`);
    } else if (node.type === 'action') {
      styles.push(`class ${nodeId} actionNode`);
    }
    
    // 选中高亮
    if (options?.selectedNodeId === node.id) {
      styles.push(`class ${nodeId} selectedNode`);
    }
    
    // 路径高亮
    if (options?.highlightPath?.includes(node.id)) {
      styles.push(`class ${nodeId} pathNode`);
    }
    
    // 添加连线
    if (parentId) {
      lines.push(`    ${parentId} --> ${nodeId}`);
    }
    
    // 递归处理子节点
    if (node.children && node.children.length > 0) {
      for (const child of node.children) {
        processNode(child, nodeId);
      }
    }
  }
  
  processNode(filteredTree);
  
  // 添加样式定义
  lines.push('    %% 样式定义');
  lines.push('    classDef orgNode fill:#3B82F6,stroke:#1E40AF,stroke-width:2px,color:#fff');
  lines.push('    classDef opNode fill:#10B981,stroke:#047857,stroke-width:2px,color:#fff');
  lines.push('    classDef actionNode fill:#F59E0B,stroke:#B45309,stroke-width:2px,color:#fff');
  lines.push('    classDef selectedNode fill:#8B5CF6,stroke:#6D28D9,stroke-width:3px,color:#fff');
  lines.push('    classDef pathNode fill:#EC4899,stroke:#BE185D,stroke-width:2px,color:#fff');
  
  // 添加样式应用
  if (styles.length > 0) {
    lines.push('    ' + [...new Set(styles)].join('\n    '));
  }
  
  return lines.join('\n');
}

export default {
  shouldShowOrganizationTree,
  canViewNode,
  filterTreeByPermission,
  getRoleDisplayName,
  getViewableNodeTypes,
  canExportReports,
  canSubmitConclusion,
  generatePermissionFilteredMermaid,
};
