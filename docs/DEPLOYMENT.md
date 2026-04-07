# GMV 智能归因系统 - 部署指南

## 1. 环境要求

- **Docker** >= 24.0
- **Docker Compose** >= 2.20
- **Node.js** >= 18（本地前端开发）
- **Python** >= 3.10（本地后端开发）

## 2. 快速启动（Docker Compose）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY 等必填项

# 2. 启动全部服务
docker-compose up --build -d

# 3. 查看健康状态
curl http://localhost:8000/health
```

服务映射：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- PostgreSQL：localhost:5432

## 3. 本地开发启动

### 后端

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=src python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认访问 http://localhost:5173，API 代理到 http://localhost:8000。

## 4. 环境变量说明

| 变量名 | 必填 | 说明 | 示例 |
|--------|------|------|------|
| `DATABASE_URL` | 是 | PostgreSQL 连接字符串 | `postgresql://user:pass@db:5432/dbname` |
| `LLM_PROVIDER` | 否 | LLM 提供商 | `claude` / `openai` / `mock` |
| `LLM_MODEL` | 否 | 模型名称 | `claude-3-opus-20240229` |
| `LLM_API_KEY` | 是（非 mock）| API 密钥 | `sk-xxx` |
| `LLM_API_BASE` | 否 | 自定义 API 基地址 | `https://api.proxy.com/v1` |
| `ALLOWED_ORIGINS` | 否 | CORS 允许域名（逗号分隔） | `http://localhost:5173,http://localhost:3000` |
| `VITE_API_BASE_URL` | 是（前端）| 后端 API 地址 | `http://localhost:8000/api/v1` |

## 5. 健康检查

后端提供 `/health` 端点，返回以下依赖状态：

```json
{
  "status": "healthy",
  "checks": {
    "indicator_tree_config": {"ok": true, "error": null},
    "upload_directory": {"ok": true, "path": "/app/uploads", "error": null},
    "playwright_chromium": {"ok": true, "error": null}
  }
}
```

## 6. 测试

```bash
# 后端测试
cd backend
PYTHONPATH=src python3 -m pytest tests/ -q

# 前端构建检查
cd frontend
npm run build
```

## 7. 常见问题

### Q1: PDF 导出失败
检查 `/health` 中 `playwright_chromium` 是否为 `true`。若部署在 Docker 中，确保 `Dockerfile` 已安装 Playwright 系统依赖和 Chromium。

### Q2: 前端无法连接后端
检查 `VITE_API_BASE_URL` 是否正确，以及 CORS 配置是否允许前端域名。

### Q3: 上传文件丢失
确保 `uploads/` 目录已挂载为持久化卷（`docker-compose.yml` 中已配置）。
