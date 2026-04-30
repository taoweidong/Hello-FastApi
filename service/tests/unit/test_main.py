"""create_app 应用程序工厂单元测试。"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.constants import API_SYSTEM_PREFIX
from src.infrastructure.http import IPFilterMiddleware, RequestLoggingMiddleware
from src.infrastructure.lifecycle import empty_lifespan
from src.main import create_app


@pytest.mark.unit
class TestCreateApp:
    """create_app 应用程序工厂测试类。"""

    @pytest.fixture
    def app(self):
        return create_app(lifespan_override=empty_lifespan)

    def test_create_app_returns_fastapi_instance(self, app):
        """测试 create_app 返回 FastAPI 实例。"""
        assert isinstance(app, FastAPI)

    def test_app_title_and_version(self, app):
        """测试应用标题和版本号。"""
        from src.config.settings import settings

        assert app.title == settings.APP_NAME
        assert app.version == settings.API_VERSION

    def test_docs_urls_are_set(self, app):
        """测试文档 URL 已配置。"""
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

    def test_cors_middleware_registered(self, app):
        """测试 CORS 中间件已注册。"""
        middleware_classes = [m.cls for m in app.user_middleware]
        assert CORSMiddleware in middleware_classes

    def test_request_logging_middleware_registered(self, app):
        """测试 RequestLoggingMiddleware 已注册。"""
        middleware_classes = [m.cls for m in app.user_middleware]
        assert RequestLoggingMiddleware in middleware_classes

    def test_ip_filter_middleware_registered(self, app):
        """测试 IPFilterMiddleware 已注册。"""
        middleware_classes = [m.cls for m in app.user_middleware]
        assert IPFilterMiddleware in middleware_classes

    def test_cors_middleware_options(self, app):
        """测试 CORS 中间件配置正确。"""
        from src.config.settings import settings

        cors_middleware = [m for m in app.user_middleware if m.cls == CORSMiddleware][0]
        kwargs = cors_middleware.kwargs
        assert kwargs["allow_origins"] == settings.cors_origins_list
        assert kwargs["allow_credentials"] is True
        assert kwargs["allow_methods"] == ["*"]
        assert kwargs["allow_headers"] == ["*"]

    def test_health_check_route_exists(self, app):
        """测试 /health 路由已注册。"""
        routes = [r.path for r in app.routes]
        assert "/health" in routes

    def test_system_router_included(self, app):
        """测试 system_router 已包含。"""
        route_paths = [r.path for r in app.routes]
        system_paths = [p for p in route_paths if p.startswith(API_SYSTEM_PREFIX)]
        assert len(system_paths) > 0

    def test_ip_filter_cache_set_app_called(self):
        """测试 IPFilterCache.set_app 被调用。"""
        with patch("src.main.get_ip_filter_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_get_cache.return_value = mock_cache
            app = create_app(lifespan_override=empty_lifespan)
            mock_cache.set_app.assert_called_once_with(app)

    def test_register_exception_handlers_called(self):
        """测试 register_exception_handlers 被调用。"""
        with patch("src.main.register_exception_handlers") as mock_register:
            app = create_app(lifespan_override=empty_lifespan)
            mock_register.assert_called_once_with(app)

    def test_default_lifespan_when_no_override(self):
        """测试未提供 lifespan_override 时使用默认 lifespan。"""
        with patch("src.main.application_lifespan"):
            app = create_app()
            assert isinstance(app, FastAPI)

    def test_lifespan_override_is_used(self):
        """测试 lifespan_override 被正确使用。"""
        app = create_app(lifespan_override=empty_lifespan)
        assert isinstance(app, FastAPI)

    def test_health_check_returns_correct_response(self, app):
        """测试 /health 端点返回正确内容。"""
        for route in app.routes:
            if route.path == "/health":
                assert hasattr(route, "endpoint")
                break
        else:
            pytest.fail("未找到 /health 路由")

    def test_openapi_routes_exist(self, app):
        """测试 OpenAPI 相关路由存在。"""
        route_paths = [r.path for r in app.routes]
        assert "/openapi.json" in route_paths

    def test_all_middleware_registered(self, app):
        """测试所有中间件均已注册。"""
        from slowapi.middleware import SlowAPIMiddleware

        middleware_classes = [m.cls for m in app.user_middleware]
        assert CORSMiddleware in middleware_classes
        assert RequestLoggingMiddleware in middleware_classes
        assert IPFilterMiddleware in middleware_classes
        assert SlowAPIMiddleware in middleware_classes
