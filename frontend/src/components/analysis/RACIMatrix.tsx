/**
 * RACI 责任矩阵展示组件
 * 
 * 展示 RACI 责任分配：
 * - R (Responsible): 执行人
 * - A (Accountable): 负责人
 * - C (Consulted): 咨询人
 * - I (Informed): 知会人
 */

import React from 'react';
import { UserCheck, UserCog, MessageCircle, Mail } from 'lucide-react';
import type { RACIMatrix } from '../../types';

interface RACIMatrixProps {
  raci: RACIMatrix;
  title?: string;
  showLegend?: boolean;
  compact?: boolean;
  className?: string;
}

/**
 * RACI 矩阵展示组件
 */
export const RACIMatrixDisplay: React.FC<RACIMatrixProps> = ({
  raci,
  title = 'RACI 责任矩阵',
  showLegend = true,
  compact = false,
  className = '',
}) => {
  const matrix = [
    {
      key: 'responsible' as const,
      label: 'R - 执行',
      description: 'Responsible',
      color: 'bg-blue-500',
      lightColor: 'bg-blue-50',
      textColor: 'text-blue-800',
      borderColor: 'border-blue-200',
      icon: UserCheck,
    },
    {
      key: 'accountable' as const,
      label: 'A - 负责',
      description: 'Accountable',
      color: 'bg-red-500',
      lightColor: 'bg-red-50',
      textColor: 'text-red-800',
      borderColor: 'border-red-200',
      icon: UserCog,
    },
    {
      key: 'consulted' as const,
      label: 'C - 咨询',
      description: 'Consulted',
      color: 'bg-amber-500',
      lightColor: 'bg-amber-50',
      textColor: 'text-amber-800',
      borderColor: 'border-amber-200',
      icon: MessageCircle,
    },
    {
      key: 'informed' as const,
      label: 'I - 知会',
      description: 'Informed',
      color: 'bg-gray-500',
      lightColor: 'bg-gray-50',
      textColor: 'text-gray-800',
      borderColor: 'border-gray-200',
      icon: Mail,
    },
  ];

  const getValue = (key: keyof RACIMatrix): string => {
    const value = raci[key];
    if (!value) return '-';
    if (Array.isArray(value)) {
      return value.length > 0 ? value.join(', ') : '-';
    }
    return value;
  };

  if (compact) {
    return (
      <div className={`grid grid-cols-4 gap-2 ${className}`}>
        {matrix.map(({ key, label, lightColor, textColor, icon: Icon }) => (
          <div
            key={key}
            className={`${lightColor} rounded-lg p-2 border ${textColor}`}
          >
            <div className="flex items-center gap-1 mb-1">
              <Icon className="w-3 h-3" />
              <span className="text-xs font-medium">{label}</span>
            </div>
            <div className="text-sm font-medium truncate">
              {getValue(key)}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 ${className}`}>
      {/* 标题 */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
        <h4 className="font-semibold text-gray-800">{title}</h4>
        {showLegend && (
          <span className="text-xs text-gray-500">
            明确优化责任归属
          </span>
        )}
      </div>

      {/* RACI 矩阵 */}
      <div className="p-4">
        <div className="grid grid-cols-4 gap-3">
          {matrix.map(({ key, label, description, color, lightColor, textColor, borderColor, icon: Icon }) => {
            const value = getValue(key);
            const hasValue = value !== '-';

            return (
              <div
                key={key}
                className={`
                  rounded-lg border-2 p-3 transition-all
                  ${hasValue ? lightColor + ' ' + borderColor : 'bg-gray-50 border-gray-200'}
                `}
              >
                {/* 头部 */}
                <div className="flex items-center gap-2 mb-2">
                  <div className={`${color} text-white w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold`}>
                    {key.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className={`text-sm font-semibold ${hasValue ? textColor : 'text-gray-600'}`}>
                      {label}
                    </div>
                    <div className="text-xs text-gray-400">{description}</div>
                  </div>
                </div>

                {/* 内容 */}
                <div className={`text-sm ${hasValue ? 'text-gray-800 font-medium' : 'text-gray-400 italic'}`}>
                  {hasValue ? (
                    <div className="space-y-1">
                      {Array.isArray(raci[key]) ? (
                        (raci[key] as string[]).map((item, idx) => (
                          <div key={idx} className="flex items-center gap-1">
                            <Icon className={`w-3 h-3 ${textColor}`} />
                            <span>{item}</span>
                          </div>
                        ))
                      ) : (
                        <div className="flex items-center gap-1">
                          <Icon className={`w-3 h-3 ${textColor}`} />
                          <span>{raci[key] as string}</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <span>未指定</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* 说明文字 */}
        {showLegend && (
          <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 space-y-1">
            <p><strong>R (执行)</strong>：具体执行优化任务的人员</p>
            <p><strong>A (负责)</strong>：对优化结果负最终责任的人（只能有一个）</p>
            <p><strong>C (咨询)</strong>：在优化过程中需要提供意见的人</p>
            <p><strong>I (知会)</strong>：需要被告知优化进展和结果的人</p>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * 简版 RACI 矩阵（用于列表展示）
 */
export const RACIMatrixCompact: React.FC<{ raci: RACIMatrix; className?: string }> = ({
  raci,
  className = '',
}) => {
  return (
    <div className={`flex items-center gap-2 text-xs ${className}`}>
      {raci.responsible && raci.responsible.length > 0 && (
        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
          R: {raci.responsible.length}人
        </span>
      )}
      {raci.accountable && (
        <span className="px-2 py-1 bg-red-100 text-red-700 rounded font-medium">
          A: {raci.accountable}
        </span>
      )}
      {raci.consulted && raci.consulted.length > 0 && (
        <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded">
          C: {raci.consulted.length}人
        </span>
      )}
      {raci.informed && raci.informed.length > 0 && (
        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded">
          I: {raci.informed.length}人
        </span>
      )}
    </div>
  );
};

export default RACIMatrixDisplay;
