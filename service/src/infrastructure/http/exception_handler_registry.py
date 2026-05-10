"""全局 HTTP 异常处理注册器。"""

import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.domain.exceptions import AppError
from src.infrastructure.common.sanitizer import safe_log_data
from src.infrastructure.logging.logger import logger


class ExceptionHandlerRegistry:
    """异常处理器注册器，统一管理业务异常、校验异常与兜底异常。"""

    def __init__(self, app: FastAPI) -> None:
        self._app = app
        self._register_handlers()

    def _register_handlers(self) -> None:
        """注册所有异常处理器。"""

        @self._app.exception_handler(AppError)
        async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
            """处理业务异常。"""
            logger.warning(f"业务异常: {exc.detail} | 路径: {request.url.path} | 方法: {request.method}")
            content: dict[str, Any] = {"code": exc.status_code, "message": str(exc.detail)}
            if exc.status_code >= 500:
                content["message"] = "服务器内部错误"
            return JSONResponse(status_code=exc.status_code, content=content)

        @self._app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
            """处理请求验证异常。"""
            errors_data = safe_log_data(exc.errors())
            logger.warning(f"参数验证失败 | 路径: {request.url.path} | 方法: {request.method} | 错误: {errors_data}")
            errors = []
            for error in exc.errors():
                errors.append({"field": ".".join(str(loc) for loc in error["loc"]), "message": error["msg"]})

            return JSONResponse(status_code=422, content={"code": 422, "message": "参数验证失败", "errors": errors})

        @self._app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
            """处理未捕获的通用异常。"""
            logger.error(
                f"未处理的异常: {safe_log_data(exc)}\n"
                f"路径: {request.url.path} | 方法: {request.method}\n"
                f"{traceback.format_exc()}"
            )
            return JSONResponse(status_code=500, content={"code": 500, "message": "服务器内部错误"})


def register_exception_handlers(app: FastAPI) -> None:
    """注册业务异常、校验异常与兜底异常处理器（兼容旧接口）。"""
    ExceptionHandlerRegistry(app)
