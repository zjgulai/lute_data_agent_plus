/**
 * 双指标树视图组件
 * 
 * 同时展示组织侧（定责）和经营侧（归因）两棵指标树
 * 支持权限过滤、节点展开/折叠、RACI 展示
 */

import React, { useState, useCallback } from 'react';
import { ChevronRight, ChevronDown, Users, BarChart3, AlertTriangle } from 'lucide-react';
import type { TreeNode, User } from '../../types';
import { shouldShowOrganizationTree, canViewNode } from '../../utils/permission';

interface TreeNodeProps {
  node: TreeNode;
  isOrgTree: boolean;
  level: number;
  user: User | null;
  selectedNodeId: string | null;
  onSelect: (node: TreeNode) => void;
  highlightPath: string[];
  isAnomaly?: boolean;
}

/**
 * 单个树节点组件
 */
const TreeNodeComponent: React.FC<TreeNodeProps> = ({
  node,
  isOrgTree,
  level,
  user,
  selectedNodeId,
  onSelect,
  highlightPath,
  isAnomaly,
}) => {
  const [isExpanded, setIsExpanded] = useState(level < 2);
  
  // 检查是否有权限查看此节点
  const canView = canViewNode(node, user);
  if (!canView && node.type === 'organization') {
    return null;
  }

  const isSelected = selectedNodeId === node.id;
  const isInPath = highlightPath.includes(node.id);
  const hasChildren = node.children && node.children.length > 0;
  
  // 节点样式
  const getNodeStyle = () => {
    if (isOrgTree || node.type === 'organization') {
      return 'bg-gradient-to-r from-blue-500 to-blue-700 text-white';
    }
    if (node.type === 'action') {
      return 'bg-gradient-to-r from-amber-500 to-amber-700 text-white';
    }
    return 'bg-gradient-to-r from-emerald-500 to-emerald-700 text-white';
  };

  const toggleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div className="ml-4">
      <div
        className={`
          inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm cursor-pointer
          transition-all duration-200 hover:scale-105 hover:shadow-lg
          ${getNodeStyle()}
          ${isSelected ? 'ring-4 ring-purple-400' : ''}
          ${isInPath ? 'ring-2 ring-pink-400' : ''}
          ${isAnomaly ? 'animate-pulse shadow-red-500/50' : ''}
        `}
        onClick={() => onSelect(node)}
      >
        {hasChildren && (
          <button
            onClick={toggleExpand}
            className="p-0.5 hover:bg-white/20 rounded transition-colors"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
        )}
        
        <span className="font-medium">{node.level_code} {node.name}</span>
        
        {node.weight && (
          <span className="text-xs bg-white/20 px-1.5 py-0.5 rounded">
            权重 {Math.round(node.weight * 100)}%
          </span>
        )}
        
        {isAnomaly && (
          <AlertTriangle className="w-4 h-4 text-yellow-300 animate-bounce" />
        )}
      </div>

      {isExpanded && hasChildren && (
        <div className="mt-2 pl-4 border-l-2 border-gray-200">
          {node.children!.map((child) => (
            <TreeNodeComponent
              key={child.id}
              node={child}
              isOrgTree={isOrgTree}
              level={level + 1}
              user={user}
              selectedNodeId={selectedNodeId}
              onSelect={onSelect}
              highlightPath={highlightPath}
              isAnomaly={isAnomaly && (child.id === 'org_sg' || child.id === 'act_member_day_participation')}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface DualTreeViewProps {
  orgTree: TreeNode;
  opTree: TreeNode;
  user: User | null;
  selectedNodeId?: string | null;
  onNodeSelect?: (node: TreeNode) => void;
  highlightPath?: string[];
  className?: string;
}

/**
 * 双指标树视图
 * 
 * 并列展示组织侧和经营侧两棵指标树
 */
export const DualTreeView: React.FC<DualTreeViewProps> = ({
  orgTree,
  opTree,
  user,
  selectedNodeId = null,
  onNodeSelect,
  highlightPath = [],
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState<'dual' | 'org' | 'op'>('dual');
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);

  const handleNodeSelect = useCallback((node: TreeNode) => {
    setSelectedNode(node);
    onNodeSelect?.(node);
  }, [onNodeSelect]);

  // 检查是否有权限查看组织树
  const showOrgTree = shouldShowOrganizationTree(user);

  // 如果没有权限看组织树，默认切换到经营侧
  React.useEffect(() => {
    if (!showOrgTree && activeTab === 'org') {
      setActiveTab('op');
    }
  }, [showOrgTree, activeTab]);

  return (
    <div className={`bg-white rounded-xl shadow-sm ${className}`}>
      {/* 标签切换 */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-800">指标树视图</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('dual')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'dual'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            双树对比
          </button>
          {showOrgTree && (
            <button
              onClick={() => setActiveTab('org')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                activeTab === 'org'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <Users className="w-4 h-4" />
              组织侧
            </button>
          )}
          <button
            onClick={() => setActiveTab('op')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'op'
                ? 'bg-emerald-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            经营侧
          </button>
        </div>
      </div>

      {/* 双树展示区域 */}
      <div className={`p-6 grid ${activeTab === 'dual' ? 'grid-cols-2' : 'grid-cols-1'} gap-6`}>
        {/* 组织侧树 */}
        {(activeTab === 'dual' || activeTab === 'org') && showOrgTree && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-blue-800 flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                【组织侧】定责树
              </h4>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                预定义层级 · 不走熵减
              </span>
            </div>
            <div className="bg-blue-50 rounded-lg p-4 max-h-96 overflow-auto">
              <TreeNodeComponent
                node={orgTree}
                isOrgTree={true}
                level={0}
                user={user}
                selectedNodeId={selectedNodeId}
                onSelect={handleNodeSelect}
                highlightPath={highlightPath}
                isAnomaly={true}
              />
            </div>
            
            {/* 组织侧说明 */}
            <div className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3">
              <strong>用途：</strong>确定责任归属，从全球 → 区域 → 国家 → 部门 → 责任人逐级下钻
            </div>
          </div>
        )}

        {/* 经营侧树 */}
        {(activeTab === 'dual' || activeTab === 'op') && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-emerald-800 flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                【经营侧】归因树
              </h4>
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                维度池 · 熵减算法驱动
              </span>
            </div>
            <div className="bg-emerald-50 rounded-lg p-4 max-h-96 overflow-auto">
              <TreeNodeComponent
                node={opTree}
                isOrgTree={false}
                level={0}
                user={user}
                selectedNodeId={selectedNodeId}
                onSelect={handleNodeSelect}
                highlightPath={highlightPath}
                isAnomaly={true}
              />
            </div>
            
            {/* 经营侧说明 */}
            <div className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3">
              <strong>用途：</strong>定位业务根因，通过 GMV = UV × CR × AOV 公式分解 + 维度池切分
            </div>
          </div>
        )}
      </div>

      {/* 选中节点详情 */}
      {selectedNode && (
        <div className="px-6 pb-6">
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h4 className="font-semibold text-purple-800 mb-2">
              选中节点：{selectedNode.level_code} {selectedNode.name}
            </h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              {selectedNode.formula && (
                <div>
                  <span className="text-gray-600">公式：</span>
                  <code className="bg-white px-2 py-1 rounded ml-2">{selectedNode.formula}</code>
                </div>
              )}
              {selectedNode.weight && (
                <div>
                  <span className="text-gray-600">权重：</span>
                  <span className="ml-2">{Math.round(selectedNode.weight * 100)}%</span>
                </div>
              )}
              {selectedNode.entropy_threshold && (
                <div>
                  <span className="text-gray-600">熵减阈值：</span>
                  <span className="ml-2">{selectedNode.entropy_threshold}</span>
                </div>
              )}
              {selectedNode.dimension_pool && (
                <div>
                  <span className="text-gray-600">维度池：</span>
                  <span className="ml-2">
                    {selectedNode.dimension_pool.map(d => d.dimension_name).join(', ')}
                  </span>
                </div>
              )}
            </div>
            
            {/* RACI 信息 */}
            {selectedNode.raci && (
              <div className="mt-4 pt-4 border-t border-purple-200">
                <h5 className="font-medium text-purple-800 mb-2">RACI 责任矩阵</h5>
                <div className="grid grid-cols-4 gap-2">
                  <div className="bg-blue-100 rounded p-2">
                    <div className="text-xs text-blue-800 font-medium">R - 执行</div>
                    <div className="text-sm">{selectedNode.raci.responsible?.join(', ') || '-'}</div>
                  </div>
                  <div className="bg-red-100 rounded p-2">
                    <div className="text-xs text-red-800 font-medium">A - 负责</div>
                    <div className="text-sm">{selectedNode.raci.accountable || '-'}</div>
                  </div>
                  <div className="bg-amber-100 rounded p-2">
                    <div className="text-xs text-amber-800 font-medium">C - 咨询</div>
                    <div className="text-sm">{selectedNode.raci.consulted?.join(', ') || '-'}</div>
                  </div>
                  <div className="bg-gray-100 rounded p-2">
                    <div className="text-xs text-gray-800 font-medium">I - 知会</div>
                    <div className="text-sm">{selectedNode.raci.informed?.join(', ') || '-'}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DualTreeView;
