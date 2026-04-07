/**
 * 角色切换器组件
 * 
 * 用于开发和演示阶段切换不同用户角色
 */

import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { useSessionStore } from '../../stores/sessionStore';
import type { UserRole } from '../../types';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface RoleSwitcherProps {
  className?: string;
}

const ROLES: { value: UserRole; label: string; color: string; description: string }[] = [
  {
    value: 'global_manager',
    label: '全局管理者',
    color: 'purple',
    description: '查看完整双组织树',
  },
  {
    value: 'regional_manager',
    label: '区域管理者',
    color: 'blue',
    description: '查看所辖区域',
  },
  {
    value: 'business_user',
    label: '业务用户',
    color: 'green',
    description: '仅查看经营侧',
  },
];

export const RoleSwitcher: React.FC<RoleSwitcherProps> = ({ className }) => {
  const { currentUser, setCurrentUser } = useSessionStore();
  const [isOpen, setIsOpen] = React.useState(false);

  if (!currentUser) return null;

  const handleRoleChange = (role: UserRole) => {
    // 根据角色设置默认权限
    const permissionsMap: Record<UserRole, string[]> = {
      global_manager: ['view_all', 'export_reports', 'submit_conclusions'],
      regional_manager: ['view_regional', 'export_reports', 'submit_conclusions'],
      business_user: ['view_operation', 'submit_conclusions'],
    };

    const regionsMap: Record<UserRole, string[]> = {
      global_manager: ['global'],
      regional_manager: ['asia_pacific'],
      business_user: [],
    };

    setCurrentUser({
      ...currentUser,
      role,
      permissions: permissionsMap[role],
      assigned_regions: regionsMap[role],
    });
    
    setIsOpen(false);
  };

  const currentRoleConfig = ROLES.find(r => r.value === currentUser.role);

  return (
    <div className={cn("relative", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-colors",
          "bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600",
          "text-gray-700 dark:text-gray-300"
        )}
      >
        <span className={cn(
          "w-2 h-2 rounded-full",
          currentRoleConfig?.color === 'purple' && "bg-purple-500",
          currentRoleConfig?.color === 'blue' && "bg-blue-500",
          currentRoleConfig?.color === 'green' && "bg-green-500"
        )} />
        <span>{currentRoleConfig?.label}</span>
        <svg
          className={cn("w-3 h-3 transition-transform", isOpen && "rotate-180")}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50 py-2">
            <div className="px-3 py-2 border-b border-gray-200 dark:border-gray-700">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                切换用户角色
              </p>
            </div>
            {ROLES.map((role) => (
              <button
                key={role.value}
                onClick={() => handleRoleChange(role.value)}
                className={cn(
                  "w-full px-3 py-2.5 flex items-start gap-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors",
                  currentUser.role === role.value && "bg-purple-50 dark:bg-purple-900/20"
                )}
              >
                <span className={cn(
                  "w-2 h-2 rounded-full mt-1.5 shrink-0",
                  role.color === 'purple' && "bg-purple-500",
                  role.color === 'blue' && "bg-blue-500",
                  role.color === 'green' && "bg-green-500"
                )} />
                <div>
                  <p className={cn(
                    "text-sm font-medium",
                    currentUser.role === role.value
                      ? "text-purple-700 dark:text-purple-400"
                      : "text-gray-700 dark:text-gray-300"
                  )}>
                    {role.label}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {role.description}
                  </p>
                </div>
                {currentUser.role === role.value && (
                  <svg
                    className="w-4 h-4 text-purple-500 ml-auto shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default RoleSwitcher;
