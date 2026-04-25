"""ASGI 配置的单元测试。"""

import pytest

from src.config.asgi import application
from src.main import app


@pytest.mark.unit
class TestASGIApplication:
    """ASGI 应用实例验证测试。"""

    def test_application_is_app(self):
        """测试 ASGI application 就是 main app 实例。"""
        assert application is app

    def test_application_has_router(self):
        """测试 application 包含路由。"""
        assert hasattr(application, "router")
        assert application.router is not None
