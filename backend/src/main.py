"""FastAPI 应用入口."""

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.algorithm import router as algorithm_router
from middleware import LoggingMiddleware
from api.export import router as export_router
from api.preview import router as preview_router
from api.session import router as session_router
from api.upload import router as upload_router
from indicator_tree import IndicatorTreeParser
from db import init_db

# 初始化数据库（默认 SQLite，便于开发和测试；生产环境通过 DATABASE_URL 使用 PostgreSQL）
_database_url = os.getenv("DATABASE_URL", "sqlite:///./gmv_attribution.db")
init_db(_database_url)

app = FastAPI(
    title="GMV 智能归因系统",
    description="指标树配置、算法计算与归因报告生成",
    version="0.1.0",
)

# 请求日志中间件
app.add_middleware(LoggingMiddleware)

# CORS 配置（生产环境通过 ALLOWED_ORIGINS 限制，默认开发通配）
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
allow_origins = [origin.strip() for origin in _allowed_origins.split(",")] if _allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(preview_router)
app.include_router(algorithm_router)
app.include_router(session_router)
app.include_router(export_router)
app.include_router(upload_router)


@app.get("/health", response_model=None)
def health_check() -> dict[str, Any]:
    """健康检查：返回各核心依赖状态."""
    config_path = Path(__file__).parent.parent / "config" / "indicator_tree.yaml"
    upload_dir = Path("/app/uploads") if os.path.exists("/app/uploads") else Path("uploads")

    # 指标树配置检查
    config_ok = False
    config_error = None
    try:
        IndicatorTreeParser.parse_file(config_path)
        config_ok = True
    except Exception as e:
        config_error = str(e)

    # 上传目录检查
    upload_ok = False
    upload_error = None
    try:
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_ok = os.access(upload_dir, os.W_OK)
    except Exception as e:
        upload_error = str(e)

    # Playwright 浏览器检查
    playwright_ok = False
    playwright_error = None
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        playwright_ok = True
    except Exception as e:
        playwright_error = str(e)

    overall = config_ok and upload_ok and playwright_ok
    return {
        "status": "healthy" if overall else "degraded",
        "checks": {
            "indicator_tree_config": {"ok": config_ok, "error": config_error},
            "upload_directory": {"ok": upload_ok, "path": str(upload_dir), "error": upload_error},
            "playwright_chromium": {"ok": playwright_ok, "error": playwright_error},
        },
    }
