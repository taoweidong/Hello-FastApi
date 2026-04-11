"""FastAPI 应用程序工厂和入口点。"""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.constants import API_SYSTEM_PREFIX
from src.api.v1 import system_router
from src.config.settings import settings
from src.infrastructure.http import RequestLoggingMiddleware, register_exception_handlers
from src.infrastructure.lifecycle import application_lifespan

LifespanFactory = Callable[[FastAPI], AbstractAsyncContextManager[Any]]


def create_app(*, lifespan_override: LifespanFactory | None = None) -> FastAPI:
    """应用程序工厂 - 创建并配置 FastAPI 应用。

    Args:
        lifespan_override: 自定义生命周期；默认执行数据库初始化与关闭。
    """
    life = lifespan_override if lifespan_override is not None else application_lifespan
    app = FastAPI(title=settings.APP_NAME, description="FastAPI + DDD + RBAC API Service", version=settings.API_VERSION, docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json", lifespan=life)

    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": settings.API_VERSION}

    app.include_router(system_router, prefix=API_SYSTEM_PREFIX)

    return app


app = create_app()
