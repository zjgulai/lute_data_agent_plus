import React, { useCallback, useEffect, useState } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { uploadApi } from '../../services/api';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface UploadedFileItem {
  file_id: string;
  original_name: string;
  file_type: string;
  file_size: number;
  parse_status: 'pending' | 'success' | 'error';
}

interface FileUploadProps {
  sessionId: string;
  className?: string;
}

const MAX_FILE_SIZE = 20 * 1024 * 1024;
const ALLOWED_TYPES = ['.pdf', '.docx', '.xlsx', '.xls'];

/**
 * 文件上传组件
 *
 * 支持拖拽和点击上传，限制文件类型和大小。
 */
export const FileUpload: React.FC<FileUploadProps> = ({ sessionId, className }) => {
  const [files, setFiles] = useState<UploadedFileItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFiles = useCallback(async () => {
    try {
      const res = await uploadApi.listFiles(sessionId);
      setFiles(res.files);
    } catch (err) {
      console.error('加载文件列表失败:', err);
    }
  }, [sessionId]);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  const handleUpload = async (file: File) => {
    setError(null);

    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_TYPES.includes(ext)) {
      setError(`不支持的文件类型: ${ext}，仅支持 ${ALLOWED_TYPES.join(', ')}`);
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('文件大小超过 20MB 限制');
      return;
    }

    setIsUploading(true);
    try {
      await uploadApi.upload(sessionId, file);
      await loadFiles();
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (fileId: string) => {
    try {
      await uploadApi.deleteFile(sessionId, fileId);
      await loadFiles();
    } catch (err) {
      console.error('删除失败:', err);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUpload(e.dataTransfer.files[0]);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUpload(e.target.files[0]);
    }
    e.target.value = '';
  };

  return (
    <div className={cn('space-y-3', className)}>
      {/* 拖拽区域 */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-4 text-center transition-colors',
          isDragging
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        )}
      >
        <input
          type="file"
          accept={ALLOWED_TYPES.join(',')}
          onChange={onFileChange}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <div className="pointer-events-none">
          <svg
            className="mx-auto h-8 w-8 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="mt-2 text-xs text-gray-600 dark:text-gray-300">
            {isUploading ? '上传中...' : '点击或拖拽文件到此处上传'}
          </p>
          <p className="mt-1 text-[10px] text-gray-400">
            支持 PDF、Word、Excel，单个文件不超过 20MB
          </p>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="text-xs text-red-600 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded">
          {error}
        </div>
      )}

      {/* 文件列表 */}
      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file) => (
            <div
              key={file.file_id}
              className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center gap-2 min-w-0">
                <FileIcon type={file.file_type} />
                <div className="min-w-0">
                  <p className="text-xs text-gray-900 dark:text-white truncate max-w-[180px]">
                    {file.original_name}
                  </p>
                  <p className="text-[10px] text-gray-500">
                    {formatSize(file.file_size)} · <StatusBadge status={file.parse_status} />
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleDelete(file.file_id)}
                className="text-gray-400 hover:text-red-500 p-1"
                title="删除"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const FileIcon: React.FC<{ type: string }> = ({ type }) => {
  const color =
    type === 'pdf'
      ? 'text-red-500'
      : type === 'docx'
      ? 'text-blue-500'
      : 'text-green-500';

  return (
    <svg className={cn('w-5 h-5 shrink-0', color)} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
};

const StatusBadge: React.FC<{ status: UploadedFileItem['parse_status'] }> = ({ status }) => {
  const map: Record<string, { text: string; cls: string }> = {
    pending: { text: '解析中', cls: 'text-yellow-600' },
    success: { text: '解析成功', cls: 'text-green-600' },
    error: { text: '解析失败', cls: 'text-red-600' },
  };
  const { text, cls } = map[status] || { text: status, cls: 'text-gray-600' };
  return <span className={cls}>{text}</span>;
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
