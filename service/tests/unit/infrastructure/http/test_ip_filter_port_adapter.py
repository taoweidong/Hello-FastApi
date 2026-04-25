"""IPFilterPortAdapter 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.http.ip_filter_port_adapter import IPFilterPortAdapter


@pytest.mark.unit
class TestIPFilterPortAdapter:
    """IPFilterPortAdapter 测试类。"""

    @pytest.fixture
    def adapter(self):
        return IPFilterPortAdapter()

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_ip_filter_cache")
    async def test_refresh_success(self, mock_get_cache, adapter):
        """测试 refresh 成功调用缓存的 refresh。"""
        mock_cache = MagicMock()
        mock_cache.refresh = AsyncMock()
        mock_get_cache.return_value = mock_cache

        await adapter.refresh()

        mock_cache.refresh.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_ip_filter_cache")
    async def test_refresh_cache_exception_silent(self, mock_get_cache, adapter):
        """测试 refresh 异常时静默处理。"""
        mock_cache = MagicMock()
        mock_cache.refresh = AsyncMock(side_effect=Exception("刷新失败"))
        mock_get_cache.return_value = mock_cache

        await adapter.refresh()

        mock_cache.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_import_exception_silent(self, adapter):
        """测试导入异常时静默处理。"""
        with patch(
            "src.infrastructure.http.ip_filter_cache.get_ip_filter_cache", side_effect=ImportError("模块不可用")
        ):
            await adapter.refresh()

    def test_adapter_is_ip_filter_port(self, adapter):
        """测试适配器继承自 IPFilterPort。"""
        from src.domain.services.cache_port import IPFilterPort

        assert isinstance(adapter, IPFilterPort)

    @pytest.mark.asyncio
    async def test_refresh_method_call_only(self, adapter):
        """测试 refresh 仅调用 get_ip_filter_cache().refresh()。"""
        with patch("src.infrastructure.http.ip_filter_cache.get_ip_filter_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_cache.refresh = AsyncMock()
            mock_get_cache.return_value = mock_cache

            await adapter.refresh()

            mock_get_cache.assert_called_once()
            mock_cache.refresh.assert_called_once()
