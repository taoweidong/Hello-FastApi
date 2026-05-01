"""应用生命周期单元测试。

测试 application_lifespan 的启动/关闭流程及 empty_lifespan。
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI

from src.infrastructure.lifecycle.lifespan import application_lifespan, empty_lifespan


@pytest.mark.unit
class TestEmptyLifespan:
    """测试 empty_lifespan 跳过初始化。"""

    @pytest.mark.asyncio
    async def test_empty_lifespan_yields_without_error(self):
        """empty_lifespan 应直接 yield 不报错。"""
        app = FastAPI()
        async with empty_lifespan(app):
            pass


@pytest.mark.unit
class TestApplicationLifespan:
    """测试 application_lifespan 的结构与流程。"""

    def test_is_async_context_manager(self):
        """application_lifespan 应返回异步生成器。"""
        app = FastAPI()
        mgr = application_lifespan(app)
        assert hasattr(mgr, "__aenter__")
        assert hasattr(mgr, "__aexit__")

    @pytest.mark.asyncio
    async def test_application_lifespan_context(self):
        """application_lifespan 应可作为异步上下文管理器使用。"""
        app = FastAPI()
        try:
            async with application_lifespan(app):
                pass
        except Exception:
            pytest.fail("application_lifespan 不应抛出异常")

    @pytest.mark.asyncio
    async def test_redis_connection_failure_is_logged_and_ignored(self):
        """Redis 连接失败时应记录警告并继续启动流程。"""
        app = FastAPI()
        with patch("src.infrastructure.lifecycle.lifespan.get_redis") as mock_get_redis:
            mock_get_redis.return_value = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
            async with application_lifespan(app):
                pass

    @pytest.mark.asyncio
    async def test_ip_filter_cache_load_failure_is_logged_and_ignored(self):
        """IP 黑白名单规则加载失败时应记录警告并继续启动流程。"""
        app = FastAPI()
        with patch("src.infrastructure.lifecycle.lifespan.get_redis") as mock_get_redis:
            mock_get_redis.return_value = AsyncMock()
            mock_ping = AsyncMock()
            mock_get_redis.return_value.ping = mock_ping
            with patch("src.infrastructure.http.ip_filter_cache.get_ip_filter_cache") as mock_cache:
                mock_cache_instance = AsyncMock()
                mock_cache_instance.load_to_app_state = AsyncMock(side_effect=RuntimeError("DB unavailable"))
                mock_cache.return_value = mock_cache_instance
                async with application_lifespan(app):
                    pass
