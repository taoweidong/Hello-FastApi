"""ExceptionHandlerRegistry 单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from src.domain.exceptions import AppError, NotFoundError, ConflictError
from src.infrastructure.http.exception_handler_registry import (
    ExceptionHandlerRegistry,
    register_exception_handlers,
)


def _make_mock_request() -> Request:
    """构造模拟的 Request 对象。"""
    scope = {"type": "http", "method": "GET", "path": "/", "headers": []}
    return Request(scope=scope)


@pytest.mark.unit
class TestExceptionHandlerRegistry:
    """异常处理器注册器测试类。"""

    def test_register_handlers_registers_app_error(self):
        """测试注册 AppError 异常处理器。"""
        app = FastAPI()
        ExceptionHandlerRegistry(app)
        assert AppError in app.exception_handlers

    def test_register_handlers_registers_validation_error(self):
        """测试注册 RequestValidationError 异常处理器。"""
        app = FastAPI()
        ExceptionHandlerRegistry(app)
        assert RequestValidationError in app.exception_handlers

    def test_register_handlers_registers_general_exception(self):
        """测试注册兜底 Exception 异常处理器。"""
        app = FastAPI()
        ExceptionHandlerRegistry(app)
        assert Exception in app.exception_handlers

    @pytest.mark.asyncio
    async def test_app_error_handler_returns_correct_response(self):
        """测试 AppError 处理器返回正确的状态码与消息。"""
        app = FastAPI()
        ExceptionHandlerRegistry(app)
        handler = app.exception_handlers[AppError]
        request = _make_mock_request()
        exc = NotFoundError("用户不存在")
        response = await handler(request, exc)
        assert response.status_code == 404
        body = response.body.decode("utf-8")
        import json

        data = json.loads(body)
        assert data["code"] == 404
        assert data["message"] == "用户不存在"

    @pytest.mark.asyncio
    async def test_app_error_handler_with_conflict(self):
        """测试 ConflictError 返回 409。"""
        app = FastAPI()
        ExceptionHandlerRegistry(app)
        handler = app.exception_handlers[AppError]
        request = _make_mock_request()
        exc = ConflictError("用户名已存在")
        response = await handler(request, exc)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_validation_error_handler_returns_422(self):
        """测试 RequestValidationError 处理器返回 422。"""
        app = FastAPI()
        ExceptionHandlerRegistry(app)
        handler = app.exception_handlers[RequestValidationError]
        request = _make_mock_request()
        exc = RequestValidationError(errors=[])
        response = await handler(request, exc)
        assert response.status_code == 422
        body = response.body.decode("utf-8")
        import json

        data = json.loads(body)
        assert data["code"] == 422
        assert data["message"] == "参数验证失败"
        assert "errors" in data

    @pytest.mark.asyncio
    async def test_general_exception_handler_returns_500(self):
        """测试兜底 Exception 处理器返回 500。"""
        app = FastAPI()
        ExceptionHandlerRegistry(app)
        handler = app.exception_handlers[Exception]
        request = _make_mock_request()
        exc = ValueError("内部错误")
        response = await handler(request, exc)
        assert response.status_code == 500
        body = response.body.decode("utf-8")
        import json

        data = json.loads(body)
        assert data["code"] == 500
        assert data["message"] == "服务器内部错误"


@pytest.mark.unit
class TestRegisterExceptionHandlers:
    """register_exception_handlers 函数测试类。"""

    def test_register_exception_handlers_function(self):
        """测试 register_exception_handlers 兼容函数正确注册所有处理器。"""
        app = FastAPI()
        register_exception_handlers(app)
        assert AppError in app.exception_handlers
        assert RequestValidationError in app.exception_handlers
        assert Exception in app.exception_handlers
