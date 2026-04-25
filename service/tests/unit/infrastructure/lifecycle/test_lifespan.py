"""应用生命周期单元测试。

测试 application_lifespan 的启动/关闭流程及 empty_lifespan。
"""

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
