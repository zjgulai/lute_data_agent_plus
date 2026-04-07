import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { TreeNode } from '../../types';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface NodeTooltipProps {
  nodeId: string;
  nodeData?: TreeNode | null;
  visible: boolean;
  x: number;
  y: number;
}

/**
 * 指标树节点 Tooltip
 *
 * 通过 Portal 渲染到 body，避免被父容器裁剪。
 */
export const NodeTooltip: React.FC<NodeTooltipProps> = ({
  nodeId,
  nodeData,
  visible,
  x,
  y,
}) => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !visible) return null;

  const typeLabel = {
    organization: '组织节点',
    operation: '经营节点',
    action: '动作指标',
  }[nodeData?.type || 'operation'];

  const typeColor = {
    organization: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    operation: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    action: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  }[nodeData?.type || 'operation'];

  return createPortal(
    <div
      className="fixed z-[100] px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-w-[240px]"
      style={{ left: x + 12, top: y + 12 }}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <span className={cn('text-[10px] px-1.5 py-0.5 rounded font-medium', typeColor)}>
          {typeLabel}
        </span>
        {nodeData?.level_code && (
          <span className="text-[10px] text-gray-400">{nodeData.level_code}</span>
        )}
      </div>
      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
        {nodeData?.name || nodeId}
      </h4>
      {nodeData?.formula && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-mono">
          公式: {nodeData.formula}
        </p>
      )}
      {nodeData?.pseudo_weight !== undefined && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          伪权重: {nodeData.pseudo_weight}
        </p>
      )}
      {nodeData?.entropy_threshold !== undefined && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          熵减阈值: {nodeData.entropy_threshold}
        </p>
      )}
      {nodeData?.data_source && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          数据源: {nodeData.data_source.db_view}.{nodeData.data_source.field}
        </p>
      )}
    </div>,
    document.body
  );
};
