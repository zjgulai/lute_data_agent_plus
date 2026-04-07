"""请求日志中间件."""

from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """记录每个请求的 method、path、status_code 和耗时."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        # 简单日志输出，生产环境可替换为 structlog / loguru
        print(
            f"[{request.method}] {request.url.path} "
            f"-> {response.status_code} ({elapsed:.3f}s)"
        )
        return response
