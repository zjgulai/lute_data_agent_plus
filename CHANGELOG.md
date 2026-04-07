# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-07

### 🎉 First Release

GMV 智能归因系统首个正式版本发布。

### ✨ Features

#### 核心功能
- **指标树配置系统**: YAML 配置、MECE 校验、公式循环检测、Mermaid 可视化
- **数据读取服务**: Excel 数据读取、多维度切片、时间序列处理
- **算法引擎**: 熵减归因、贡献度计算、交叉维度分析
- **状态机 + LLM Orchestrator**: 自动/手动双模式、Tool Calling、结构化结论

#### 前端交互
- **三栏式布局**: 时间轴、指标树、详情区
- **D3.js 动态时间轴**: GMV 面积图、环比标红、里程碑检测、缩放拖拽
- **归因链展示**: 底部归因路径可视化
- **交叉维度面板**: 异步结果展示
- **节点 Tooltip**: 悬停详情展示
- **时间轴-树联动**: 双向交互高亮
- **权限自适应**: 分析师/业务/高管三角色视图
- **全局 Error Boundary**: 错误捕获与友好提示

#### 报告与导出
- **Word 导出**: python-docx 生成专业报告
- **PDF 导出**: Playwright + 模板渲染
- **外部文件上传**: PDF/Word/Excel 解析与 LLM 引用

#### 数据持久化
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **会话落库**: 会话、步骤、结论全链路持久化
- **报告后备**: 内存缺失时从数据库恢复

#### 运维与监控
- **健康检查**: `/health` 端点含多子项检查
- **请求日志**: 中间件记录请求详情
- **部署文档**: Docker Compose 完整配置

### 🧪 Testing

- 后端单元测试: 118 项 ✅
- 集成测试: 8 项 ✅
- 性能测试: 8 项 ✅
  - 熵减计算 < 2s (100 子节点)
  - 贡献度计算 < 0.5s (1000 条数据)
  - 交叉维度 < 1s (100ms 超时限流)

### 🐳 Deployment

- Docker Compose 完整支持
- 前后端分离部署
- 自动健康检查与重启

### 📚 Documentation

- 完整 PRD 文档
- API 文档 (OpenAPI/Swagger)
- 部署指南
- 开发环境配置

### 🔧 Tech Stack

**Backend:**
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0
- Pandas + NumPy
- Playwright (PDF)
- Pytest

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS
- D3.js
- Mermaid.js
- Zustand (State)
- Vite

**Infrastructure:**
- Docker + Docker Compose
- PostgreSQL / SQLite
- GitHub Actions CI/CD

## [Unreleased]

### Planned
- [ ] 前端代码分割优化
- [ ] Sentry 错误监控集成
- [ ] 骨架屏加载态
- [ ] 更多 LLM Provider 支持
