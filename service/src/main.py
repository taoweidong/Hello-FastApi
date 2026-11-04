"""FastAPI 应用程序工厂和入口点。"""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api.constants import API_SYSTEM_PREFIX
from src.api.v1 import system_router
from src.config.settings import UPLOAD_DIR, settings
from src.infrastructure.http import (
    IPFilterMiddleware,
    LoginRateLimitMiddleware,
    RequestLoggingMiddleware,
    get_ip_filter_cache,
    register_exception_handlers,
)
from src.infrastructure.http.limiter import limiter, rate_limit_exceeded_handler
from src.infrastructure.lifecycle import application_lifespan

LifespanFactory = Callable[[FastAPI], AbstractAsyncContextManager[Any]]


def create_app(*, lifespan_override: LifespanFactory | None = None) -> FastAPI:
    """应用程序工厂 - 创建并配置 FastAPI 应用。

    Args:
        lifespan_override: 自定义生命周期；默认执行数据库初始化与关闭。
    """
    life = lifespan_override if lifespan_override is not None else application_lifespan
    # 生产环境不暴露 API 文档与 OpenAPI schema（未认证访问者可借此获取全部路由与 DTO 结构）
    expose_docs = not settings.is_production
    app = FastAPI(
        title=settings.APP_NAME,
        description="FastAPI + DDD + RBAC API Service",
        version=settings.API_VERSION,
        docs_url="/docs" if expose_docs else None,
        redoc_url="/redoc" if expose_docs else None,
        openapi_url="/openapi.json" if expose_docs else None,
        lifespan=life,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(IPFilterMiddleware)
    # 登录/注册专属限流（防爆破），在 SlowAPI 全局限流之外独立生效
    app.add_middleware(LoginRateLimitMiddleware)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)

    # 设置 IPFilterCache 的 app 引用，供后续 refresh 使用
    get_ip_filter_cache().set_app(app)

    register_exception_handlers(app)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": settings.API_VERSION}

    app.include_router(system_router, prefix=API_SYSTEM_PREFIX)

    # 挂载上传静态资源（头像等，目录在配置加载时已创建）
    app.mount("/media", StaticFiles(directory=str(UPLOAD_DIR)), name="media")

    return app


app = create_app()
