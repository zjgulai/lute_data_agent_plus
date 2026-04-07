# GMV 智能归因系统

[![CI/CD](https://github.com/YOUR_USERNAME/gmv-attribution/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/gmv-attribution/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 基于熵减算法的 GMV (Gross Merchandise Value) 智能归因分析系统

## 🌟 核心特性

- **🔍 智能归因**: 基于熵减算法的多维度归因分析，自动识别 GMV 波动根因
- **🤖 LLM 驱动**: 集成大语言模型，提供自然语言交互和智能分析建议
- **📊 可视化**: D3.js 动态时间轴 + Mermaid 指标树，直观展示分析链路
- **👥 权限自适应**: 分析师/业务/高管三角色，自动适配界面复杂度
- **📄 报告导出**: 一键生成 Word/PDF 专业分析报告
- **📤 文件解析**: 支持上传 PDF/Word/Excel 文件供 LLM 分析引用

## 🚀 快速开始

### Docker Compose (推荐)

```bash
# 克隆项目
git clone https://github.com/YOUR_USERNAME/gmv-attribution.git
cd gmv-attribution

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 LLM API Key

# 启动服务
docker-compose up -d

# 访问应用
open http://localhost:3000
```

### 本地开发

**后端:**
```bash
cd backend
pip install -r requirements.txt

# 开发模式启动
PYTHONPATH=src python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

## 🏗️ 架构概览

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend      │     │     Backend      │     │   External      │
│   React + TS    │◄───►│   FastAPI        │◄───►│   LLM API       │
│   D3.js         │     │   SQLAlchemy     │     │   (Claude)      │
│   Mermaid       │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   Database       │
                        │   PostgreSQL/    │
                        │   SQLite         │
                        └──────────────────┘
```

### 核心模块

| 模块 | 技术 | 功能 |
|------|------|------|
| 指标树 | YAML + Pydantic | 树形配置、MECE 校验、公式检测 |
| 算法引擎 | Pandas + NumPy | 熵减归因、贡献度、交叉维度 |
| 状态机 | Python State Machine | 归因流程控制 |
| LLM Orchestrator | Tool Calling | 自动/手动双模式分析 |
| D3 时间轴 | D3.js | GMV 趋势、环比、里程碑 |

## 📊 功能演示

### 1. 指标树可视化
- YAML 配置指标树结构
- Mermaid 自动渲染
- 支持公式和伪权重节点

### 2. 智能归因分析
- 选择时间范围
- 系统自动下钻分析
- LLM 生成分析结论

### 3. 交叉维度分析
- 异步计算避免阻塞
- 自动识别显著组合
- 紫色高亮异常项

### 4. 报告导出
- 一键 Word/PDF 导出
- 专业报告模板
- 包含完整分析链路

## 🧪 测试

```bash
# 后端测试
cd backend
PYTHONPATH=src python3 -m pytest tests/ -v

# 前端构建测试
cd frontend
npm run build
```

**测试覆盖:**
- ✅ 118 项后端单元测试
- ✅ 8 项集成测试
- ✅ 8 项性能基准测试

## 📚 文档

- [PRD 文档](./docs/PRD.md) - 产品需求文档
- [部署指南](./docs/DEPLOYMENT.md) - 详细部署说明
- [项目状态](./docs/PROJECT_STATUS.md) - 开发进度跟踪
- [API 文档](http://localhost:8000/docs) - Swagger UI (启动后访问)

## 🔧 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 | `sqlite:///./gmv_attribution.db` |
| `LLM_PROVIDER` | LLM 提供商 | `claude` |
| `LLM_API_KEY` | API 密钥 | - |
| `LLM_MODEL` | 模型名称 | `claude-3-5-sonnet-20241022` |

完整配置见 [.env.example](./.env.example)

## 🐳 Docker 镜像

```bash
# 拉取镜像
docker pull YOUR_USERNAME/gmv-attribution-backend:latest
docker pull YOUR_USERNAME/gmv-attribution-frontend:latest

# 或使用 docker-compose
docker-compose up -d
```

## 🛣️ 路线图

- [x] 指标树配置系统
- [x] 熵减算法引擎
- [x] LLM Orchestrator
- [x] D3.js 时间轴
- [x] 报告导出 (Word/PDF)
- [x] 文件上传解析
- [x] 数据库持久化
- [ ] 更多 LLM Provider 支持
- [ ] 实时监控告警
- [ ] 多租户支持

## 🤝 贡献

欢迎提交 Issue 和 PR！

1. Fork 项目
2. 创建分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

[MIT License](./LICENSE)

## 🙏 致谢

- Claude / Kimi Code CLI - AI 辅助开发
- FastAPI - 高性能 Python Web 框架
- D3.js - 数据可视化库
- Mermaid.js - 图表渲染

---

<p align="center">
  Made with ❤️ by GMV Attribution Team
</p>
