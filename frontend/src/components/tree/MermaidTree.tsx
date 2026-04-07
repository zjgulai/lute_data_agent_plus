import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { TreeNode, User } from '../../types';
import { generatePermissionFilteredMermaid } from '../../utils/permission';
import { NodeTooltip } from './NodeTooltip';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface MermaidTreeProps {
  // Mermaid 图语法（可选，与 tree + user 二选一）
  mermaidCode?: string;
  // 指标树数据（用于权限过滤）
  tree?: TreeNode;
  // 当前用户（用于权限过滤）
  user?: User | null;
  // 是否启用权限过滤
  enablePermissionFilter?: boolean;
  // 选中的节点ID
  selectedNodeId?: string | null;
  // 节点点击回调
  onNodeClick?: (nodeId: string) => void;
  // 高亮路径
  highlightedPath?: string[];
  // 自定义类名
  className?: string;
}

/**
 * Mermaid 指标树组件
 * 
 * 使用 Mermaid.js 渲染指标树图
 * 支持节点点击、选中高亮、权限过滤
 */
export const MermaidTree: React.FC<MermaidTreeProps> = ({
  mermaidCode: externalCode,
  tree,
  user,
  enablePermissionFilter = false,
  selectedNodeId,
  onNodeClick,
  highlightedPath,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgContent, setSvgContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ visible: boolean; x: number; y: number; nodeId: string }>({
    visible: false,
    x: 0,
    y: 0,
    nodeId: '',
  });

  // 生成最终的 Mermaid 代码
  const mermaidCode = React.useMemo(() => {
    // 如果启用了权限过滤且有 tree 和 user，生成过滤后的代码
    if (enablePermissionFilter && tree && user) {
      return generatePermissionFilteredMermaid(tree, user, { selectedNodeId, highlightPath: highlightedPath });
    }
    // 否则使用外部代码
    return externalCode || '';
  }, [enablePermissionFilter, tree, user, externalCode, selectedNodeId, highlightedPath]);

  // 初始化 Mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      securityLevel: 'loose',
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
      },
    });
  }, []);

  // 渲染 Mermaid 图
  useEffect(() => {
    const renderMermaid = async () => {
      if (!mermaidCode || !containerRef.current) return;

      try {
        setError(null);
        
        // 生成唯一ID
        const id = `mermaid-${Date.now()}`;
        
        // 渲染图表
        const { svg } = await mermaid.render(id, mermaidCode);
        
        setSvgContent(svg);
      } catch (err) {
        setError(err instanceof Error ? err.message : '渲染失败');
        console.error('Mermaid render error:', err);
      }
    };

    renderMermaid();
  }, [mermaidCode]);

  // 处理节点点击
  useEffect(() => {
    if (!containerRef.current || !svgContent) return;

    const container = containerRef.current;
    
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      
      // 查找最近的节点元素
      const nodeElement = target.closest('.node');
      if (nodeElement) {
        // 提取节点ID（移除 flowchart- 前缀）
        const rawId = nodeElement.id || '';
        const nodeId = rawId
          .replace(/^flowchart-/, '')
          .replace(/-_/, '_')
          .replace(/-$/, '');
        
        if (nodeId) {
          onNodeClick?.(nodeId);
        }
      }
    };

    container.addEventListener('click', handleClick);
    
    return () => {
      container.removeEventListener('click', handleClick);
    };
  }, [svgContent, onNodeClick]);

  // 高亮选中节点和路径
  useEffect(() => {
    if (!containerRef.current || !svgContent) return;

    // 移除所有高亮
    const allNodes = containerRef.current.querySelectorAll('.node');
    allNodes.forEach(node => {
      (node as HTMLElement).style.filter = '';
      (node as HTMLElement).style.transform = '';
      (node as HTMLElement).style.stroke = '';
      (node as HTMLElement).style.strokeWidth = '';
    });

    // 高亮路径节点
    highlightedPath?.forEach((nodeId) => {
      const pathNode = containerRef.current?.querySelector(
        `#flowchart-${nodeId}, [id*="${nodeId}"]`
      );
      if (pathNode) {
        const el = pathNode as HTMLElement;
        el.style.filter = 'drop-shadow(0 0 6px rgba(245, 158, 11, 0.6))';
        el.style.stroke = '#F59E0B';
        el.style.strokeWidth = '3px';
      }
    });

    // 高亮选中节点（覆盖路径样式）
    if (selectedNodeId) {
      const selectedNode = containerRef.current.querySelector(
        `#flowchart-${selectedNodeId}, [id*="${selectedNodeId}"]`
      );
      if (selectedNode) {
        (selectedNode as HTMLElement).style.filter = 'drop-shadow(0 0 8px rgba(139, 92, 246, 0.6))';
        (selectedNode as HTMLElement).style.transform = 'scale(1.02)';
        (selectedNode as HTMLElement).style.transformOrigin = 'center';
        (selectedNode as HTMLElement).style.transition = 'all 0.2s ease';
        (selectedNode as HTMLElement).style.stroke = '#8B5CF6';
        (selectedNode as HTMLElement).style.strokeWidth = '3px';
      }
    }
  }, [svgContent, selectedNodeId, highlightedPath]);

  // 节点悬停 Tooltip
  useEffect(() => {
    if (!containerRef.current || !svgContent) return;
    const container = containerRef.current;

    const handleEnter = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const nodeElement = target.closest('.node') as HTMLElement | null;
      if (!nodeElement) return;
      const rawId = nodeElement.id || '';
      const nodeId = rawId.replace(/^flowchart-/, '').replace(/-_/, '_').replace(/-$/, '');
      if (!nodeId) return;
      setTooltip({ visible: true, x: e.clientX, y: e.clientY, nodeId });
    };

    const handleMove = (e: MouseEvent) => {
      setTooltip((t) => (t.visible ? { ...t, x: e.clientX, y: e.clientY } : t));
    };

    const handleLeave = (e: MouseEvent) => {
      const related = e.relatedTarget as HTMLElement | null;
      if (!related || !related.closest('.node')) {
        setTooltip((t) => ({ ...t, visible: false }));
      }
    };

    container.addEventListener('mouseenter', handleEnter, true);
    container.addEventListener('mousemove', handleMove, true);
    container.addEventListener('mouseleave', handleLeave, true);

    return () => {
      container.removeEventListener('mouseenter', handleEnter, true);
      container.removeEventListener('mousemove', handleMove, true);
      container.removeEventListener('mouseleave', handleLeave, true);
    };
  }, [svgContent]);

  if (error) {
    return (
      <div className={cn(
        "p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg",
        className
      )}>
        <p className="text-sm text-red-600 dark:text-red-400">
          图表渲染失败: {error}
        </p>
      </div>
    );
  }

  if (!mermaidCode) {
    return (
      <div className={cn(
        "flex items-center justify-center text-gray-400",
        className
      )}>
        暂无数据
      </div>
    );
  }

  // 从 tree 中查找节点数据
  const findNodeData = (nodeId: string): TreeNode | undefined => {
    if (!tree) return undefined;
    const search = (node: TreeNode): TreeNode | undefined => {
      if (node.id === nodeId) return node;
      for (const child of node.children || []) {
        const found = search(child);
        if (found) return found;
      }
      return undefined;
    };
    return search(tree);
  };

  return (
    <>
      <div
        ref={containerRef}
        className={cn(
          "w-full h-full flex items-center justify-center overflow-auto",
          className
        )}
        dangerouslySetInnerHTML={{ __html: svgContent }}
      />
      <NodeTooltip
        nodeId={tooltip.nodeId}
        nodeData={findNodeData(tooltip.nodeId)}
        visible={tooltip.visible}
        x={tooltip.x}
        y={tooltip.y}
      />
    </>
  );
};

// 示例指标树数据生成器
export const generateSampleMermaidCode = (): string => {
  return `graph TD
    %% 根节点
    GMV["<b>GMV</b><br/>下滑 20%<br/>-200万"]
    
    %% 第一层：组织侧 + 经营侧
    GMV --> ORG["<b>组织侧</b><br/>定责"]
    GMV --> OPS["<b>经营侧</b><br/>找因"]
    
    %% 组织侧
    ORG --> US["<b>美国</b><br/>-198万<br/>熵减 74%"]
    ORG --> CN["中国<br/>+10万"]
    ORG --> EU["欧洲<br/>-12万"]
    ORG --> APAC["亚太<br/>0"]
    
    %% 经营侧
    OPS --> USER["<b>用户</b>"]
    OPS --> PROD["<b>产品</b>"]
    OPS --> MKT["<b>营销</b>"]
    
    %% 用户维度
    USER --> UV["UV<br/>-20%"]
    USER --> CR["转化率<br/>-10%"]
    USER --> AOV["客单价<br/>+11%"]
    
    %% UV 拆解
    UV --> NEW["新客UV<br/>-5万"]
    UV --> OLD["老客UV<br/>-12万"]
    
    %% 样式定义
    classDef root fill:#2563EB,stroke:#1D4ED8,color:#fff,stroke-width:3px
    classDef org fill:#DC2626,stroke:#B91C1C,color:#fff,stroke-width:2px
    classDef ops fill:#059669,stroke:#047857,color:#fff,stroke-width:2px
    classDef action fill:#7C3AED,stroke:#6D28D9,color:#fff,stroke-width:2px,stroke-dasharray: 5 5
    classDef normal fill:#F3F4F6,stroke:#9CA3AF,color:#374151
    
    class GMV root
    class ORG,US org
    class OPS,USER,PROD,MKT ops
    class UV,CR,AOV,NEW,OLD action
    class CN,EU,APAC normal`;
};

// 从 TreeNode 生成 Mermaid 代码
export const generateMermaidFromTree = (
  node: TreeNode,
  _selectedNodeId?: string,
  _highlightedNodes?: string[]
): string => {
  const lines: string[] = ['graph TD'];
  const styles: string[] = [];
  
  const processNode = (n: TreeNode, parentId?: string) => {
    const nodeId = n.id.replace(/[^a-zA-Z0-9]/g, '_');
    const displayName = n.name || n.id;
    
    // 节点定义（用于生成 Mermaid 语法）- 此处不直接使用，保留用于未来扩展
    void `${nodeId}["${displayName}"]`;
    
    // 根据节点类型添加样式类
    if (n.type === 'organization') {
      styles.push(`class ${nodeId} org`);
    } else if (n.type === 'operation') {
      styles.push(`class ${nodeId} ops`);
    } else if (n.type === 'action') {
      styles.push(`class ${nodeId} action`);
    }
    
    // 如果是根节点，添加 root 样式
    if (!parentId) {
      styles.push(`class ${nodeId} root`);
    }
    
    // 添加连线
    if (parentId) {
      lines.push(`    ${parentId} --> ${nodeId}`);
    }
    
    // 递归处理子节点
    if (n.children && n.children.length > 0) {
      for (const child of n.children) {
        processNode(child, nodeId);
      }
    }
  };
  
  processNode(node);
  
  // 添加样式定义
  lines.push('    %% 样式定义');
  lines.push('    classDef root fill:#2563EB,stroke:#1D4ED8,color:#fff,stroke-width:3px');
  lines.push('    classDef org fill:#DC2626,stroke:#B91C1C,color:#fff,stroke-width:2px');
  lines.push('    classDef ops fill:#059669,stroke:#047857,color:#fff,stroke-width:2px');
  lines.push('    classDef action fill:#7C3AED,stroke:#6D28D9,color:#fff,stroke-width:2px,stroke-dasharray: 5 5');
  lines.push('    classDef normal fill:#F3F4F6,stroke:#9CA3AF,color:#374151');
  
  // 添加样式应用
  if (styles.length > 0) {
    lines.push('    ' + [...new Set(styles)].join('\n    '));
  }
  
  return lines.join('\n');
};

export default MermaidTree;
