# GMV 智能归因系统 v1.0.0 发布说明

## 🎉 正式发布

GMV 智能归因系统首个正式版本，基于熵减算法的智能归因分析平台。

---

## ✨ 核心功能

### 1. 指标树配置系统
- YAML 驱动配置
- MECE 完整性校验
- 公式循环依赖检测
- Mermaid 自动可视化

### 2. 算法引擎
- **熵减归因**: 自动识别 GMV 波动根因
- **贡献度计算**: 精确量化各维度贡献
- **交叉维度分析**: 异步计算显著组合

### 3. LLM Orchestrator
- 自动模式: 快速分析 (3-5秒)
- 手动模式: 每步解释详情
- Tool Calling 工具调用
- 结构化结论输出

### 4. 前端交互
- **三栏式布局**: 时间轴 | 指标树 | 详情区
- **D3.js 时间轴**: GMV趋势、环比标红、里程碑
- **权限自适应**: 分析师/业务/高管三角色
- **联动高亮**: 时间轴与指标树双向交互

### 5. 报告与导出
- Word 专业报告导出
- PDF 报告导出 (Playwright)
- 外部文件上传解析 (PDF/Word/Excel)

### 6. 数据持久化
- SQLite (开发) / PostgreSQL (生产)
- 会话、步骤、结论全链路落库
- 报告导出数据库后备

---

## 🧪 测试覆盖

| 类型 | 数量 | 状态 |
|------|------|------|
| 后端单元测试 | 118 | ✅ 通过 |
| 集成测试 | 8 | ✅ 通过 |
| 性能测试 | 8 | ✅ 通过 |

**性能指标:**
- 熵减计算 (100子节点): < 2s
- 贡献度计算 (1000条数据): < 0.5s
- 交叉维度 (100ms超时限流): < 1s

---

## 🐳 部署方式

### 方式一: Docker Compose (推荐)

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/gmv-attribution.git
cd gmv-attribution

# 2. 配置环境
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY

# 3. 启动服务
docker-compose up -d

# 4. 访问
open http://localhost:3000
```

### 方式二: 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
PYTHONPATH=src uvicorn src.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

---

## 📁 项目结构

```
gmv-attribution/
├── backend/              # FastAPI 后端
│   ├── src/
│   │   ├── indicator_tree/
│   │   ├── algorithm/
│   │   ├── state_machine/
│   │   ├── llm/
│   │   ├── db/
│   │   └── api/
│   ├── tests/
│   └── Dockerfile
├── frontend/             # React 前端
│   ├── src/
│   │   ├── components/
│   │   ├── stores/
│   │   └── services/
│   └── Dockerfile
├── docs/                 # 文档
│   ├── PRD.md
│   ├── DEPLOYMENT.md
│   └── PROJECT_STATUS.md
├── docker-compose.yml
└── .github/workflows/    # CI/CD
```

---

## 🔧 技术栈

**后端:**
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- Pandas + NumPy
- Playwright

**前端:**
- React 18 + TypeScript
- Tailwind CSS
- D3.js
- Mermaid.js
- Zustand
- Vite

**基础设施:**
- Docker + Docker Compose
- PostgreSQL / SQLite
- GitHub Actions

---

## 📝 配置说明

### 必需环境变量

```bash
# LLM 配置
LLM_API_KEY=your-api-key
LLM_PROVIDER=claude
LLM_MODEL=claude-3-5-sonnet-20241022

# 数据库 (可选，默认 SQLite)
DATABASE_URL=postgresql://user:pass@localhost:5432/gmv_attribution
```

---

## 🙏 致谢

- 开发: Claude / Kimi Code CLI
- 框架: FastAPI, React
- 可视化: D3.js, Mermaid.js

---

## 📄 许可证

MIT License

---

**完整文档:** [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)  
**问题反馈:** [GitHub Issues](../../issues)

*发布日期: 2026-04-07*
