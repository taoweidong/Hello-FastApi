"""缓存端口接口的单元测试。

测试 CachePort 和 IPFilterPort 抽象基类的方法签名和返回类型。
"""

from datetime import datetime

import pytest

from src.domain.services.cache_port import CachePort, IPFilterPort


class ConcreteCachePort(CachePort):
    """用于测试的 CachePort 最小化具体实现。"""

    async def add_token_to_blacklist(self, token: str, expires_at: datetime) -> bool:
        return True

    async def is_token_blacklisted(self, token: str) -> bool:
        return False

    async def get_user_permissions(self, user_id: str) -> list[dict] | None:
        return None

    async def set_user_permissions(self, user_id: str, permissions: list[dict]) -> bool:
        return True

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        return True

    async def get_user_info(self, user_id: str) -> dict | None:
        return None

    async def set_user_info(self, user_id: str, info: dict) -> bool:
        return True

    async def invalidate_user_info(self, user_id: str) -> bool:
        return True

    async def get_all_menus(self) -> list[dict] | None:
        return None

    async def set_all_menus(self, menus: list[dict]) -> bool:
        return True

    async def invalidate_all_menus(self) -> bool:
        return True


class ConcreteIPFilterPort(IPFilterPort):
    """用于测试的 IPFilterPort 最小化具体实现。"""

    async def refresh(self) -> None:
        pass


@pytest.mark.unit
class TestCachePort:
    """CachePort 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            CachePort()  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        port = ConcreteCachePort()
        assert port is not None
        assert isinstance(port, CachePort)

    # ---- Token 黑名单 ----

    @pytest.mark.asyncio
    async def test_add_token_to_blacklist_returns_bool(self):
        """测试 add_token_to_blacklist 返回布尔值。"""
        port = ConcreteCachePort()
        result = await port.add_token_to_blacklist("token123", datetime(2030, 1, 1))
        assert isinstance(result, bool)
        assert result is True

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_returns_bool(self):
        """测试 is_token_blacklisted 返回布尔值。"""
        port = ConcreteCachePort()
        result = await port.is_token_blacklisted("token123")
        assert isinstance(result, bool)

    # ---- 用户权限缓存 ----

    @pytest.mark.asyncio
    async def test_get_user_permissions_returns_list_or_none(self):
        """测试 get_user_permissions 返回列表或 None。"""
        port = ConcreteCachePort()
        result = await port.get_user_permissions("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_user_permissions_returns_bool(self):
        """测试 set_user_permissions 返回布尔值。"""
        port = ConcreteCachePort()
        result = await port.set_user_permissions("user-1", [])
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_invalidate_user_permissions_returns_bool(self):
        """测试 invalidate_user_permissions 返回布尔值。"""
        port = ConcreteCachePort()
        result = await port.invalidate_user_permissions("user-1")
        assert isinstance(result, bool)

    # ---- 用户信息缓存 ----

    @pytest.mark.asyncio
    async def test_get_user_info_returns_dict_or_none(self):
        """测试 get_user_info 返回字典或 None。"""
        port = ConcreteCachePort()
        result = await port.get_user_info("user-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_user_info_returns_bool(self):
        """测试 set_user_info 返回布尔值。"""
        port = ConcreteCachePort()
        result = await port.set_user_info("user-1", {"username": "admin"})
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_invalidate_user_info_returns_bool(self):
        """测试 invalidate_user_info 返回布尔值。"""
        port = ConcreteCachePort()
        result = await port.invalidate_user_info("user-1")
        assert isinstance(result, bool)

    # ---- 菜单全表缓存 ----

    @pytest.mark.asyncio
    async def test_get_all_menus_returns_list_or_none(self):
        """测试 get_all_menus 返回列表或 None。"""
        port = ConcreteCachePort()
        result = await port.get_all_menus()
        assert result is None

    @pytest.mark.asyncio
    async def test_set_all_menus_returns_bool(self):
        """测试 set_all_menus 返回布尔值。"""
        port = ConcreteCachePort()
        result = await port.set_all_menus([])
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_invalidate_all_menus_returns_bool(self):
        """测试 invalidate_all_menus 返回布尔值。"""
        port = ConcreteCachePort()
        result = await port.invalidate_all_menus()
        assert isinstance(result, bool)


@pytest.mark.unit
class TestIPFilterPort:
    """IPFilterPort 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            IPFilterPort()  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        port = ConcreteIPFilterPort()
        assert port is not None
        assert isinstance(port, IPFilterPort)

    # ---- refresh ----

    @pytest.mark.asyncio
    async def test_refresh_executes_without_error(self):
        """测试 refresh 方法可以正常执行。"""
        port = ConcreteIPFilterPort()
        await port.refresh()
