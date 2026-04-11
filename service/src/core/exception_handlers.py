"""全局 HTTP 异常处理注册。"""

import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.exceptions import AppException
from src.core.logger import logger


def register_exception_handlers(app: FastAPI) -> None:
    """注册业务异常、校验异常与兜底异常处理器。"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.status_code, "message": str(exc.detail)})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"code": 422, "message": "参数验证失败", "errors": exc.errors()})

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"未处理的异常: {exc}\n{traceback.format_exc()}")
        return JSONResponse(status_code=500, content={"code": 500, "message": "服务器内部错误"})
