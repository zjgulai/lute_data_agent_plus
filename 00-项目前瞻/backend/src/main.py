"""FastAPI 应用入口."""

from fastapi import FastAPI

from api.preview import router as preview_router

app = FastAPI(
    title="GMV 智能归因系统",
    description="指标树配置、算法计算与归因报告生成",
    version="0.1.0",
)

app.include_router(preview_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
