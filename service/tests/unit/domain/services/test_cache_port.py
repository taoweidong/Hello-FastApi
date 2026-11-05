"""缓存端口接口的单元测试。

测试按消费方拆分后的窄端口（TokenRevocationPort / UserCachePort / MenuCachePort /
DictCachePort）、聚合端口 CachePort、在线会话端口 OnlineSessionStore 与 IPFilterPort
的抽象契约，以及 UserCachePort 批量失效默认实现的退化语义。
"""

from datetime import datetime
from typing import Any

import pytest

from src.domain.services.cache_port import (
    CachePort,
    DictCachePort,
    IPFilterPort,
    MenuCachePort,
    TokenRevocationPort,
    UserCachePort,
)
from src.domain.services.online_session_port import OnlineSessionStore


class ConcreteTokenRevocation(TokenRevocationPort):
    """TokenRevocationPort 的最小实现，并作为聚合端口的完整实现基座。"""

    def __init__(self) -> None:
        self.blacklisted_hashes: list[str] = []

    async def add_token_to_blacklist(self, token: str, expires_at: datetime) -> bool:
        return True

    async def is_token_blacklisted(self, token: str) -> bool:
        return False

    async def blacklist_token_hash(self, token_hash: str, expires_at: datetime) -> bool:
        self.blacklisted_hashes.append(token_hash)
        return True


class ConcreteUserCache(UserCachePort):
    """UserCachePort 的最小实现，记录失效调用顺序。"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get_user_permissions(self, user_id: str) -> list[dict] | None:
        return None

    async def set_user_permissions(self, user_id: str, permissions: list[dict]) -> bool:
        self.calls.append(f"set:perms:{user_id}")
        return True

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        self.calls.append(f"drop:perms:{user_id}")
        return True

    async def get_user_info(self, user_id: str) -> dict | None:
        return None

    async def set_user_info(self, user_id: str, info: dict) -> bool:
        return True

    async def invalidate_user_info(self, user_id: str) -> bool:
        self.calls.append(f"drop:info:{user_id}")
        return True


class ConcreteMenuCache(MenuCachePort):
    """MenuCachePort 的最小实现。"""

    async def get_all_menus(self) -> list[dict] | None:
        return None

    async def set_all_menus(self, menus: list[dict]) -> bool:
        return True

    async def invalidate_all_menus(self) -> bool:
        return True


class ConcreteDictCache(DictCachePort):
    """DictCachePort 的最小实现。"""

    async def get_dict_items(self, dict_name: str) -> list[dict[str, Any]] | None:
        return None

    async def set_dict_items(self, dict_name: str, items: list[dict[str, Any]]) -> bool:
        return True

    async def invalidate_dict(self, dict_name: str) -> bool:
        return True


class ConcreteCachePort(ConcreteTokenRevocation, ConcreteUserCache, ConcreteMenuCache, ConcreteDictCache, CachePort):
    """聚合端口 CachePort 的具体实现（组合四个窄端口实现）。"""


class ConcreteOnlineSessionStore(OnlineSessionStore):
    """OnlineSessionStore 的最小实现。"""

    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}

    async def set_online_user(self, session_key: str, info: dict[str, Any], expires_at: datetime) -> bool:
        self.sessions[session_key] = info
        return True

    async def get_online_user(self, session_key: str) -> dict[str, Any] | None:
        return self.sessions.get(session_key)

    async def get_online_users(self) -> list[dict[str, Any]]:
        return [{**info, "id": key} for key, info in self.sessions.items()]

    async def delete_online_user(self, session_key: str) -> bool:
        return self.sessions.pop(session_key, None) is not None


class ConcreteIPFilterPort(IPFilterPort):
    """用于测试的 IPFilterPort 最小化具体实现。"""

    async def refresh(self) -> None:
        pass


@pytest.mark.unit
class TestNarrowPorts:
    """窄端口各自的抽象契约。"""

    @pytest.mark.parametrize("port", [TokenRevocationPort, UserCachePort, MenuCachePort, DictCachePort])
    def test_cannot_instantiate_abc_directly(self, port):
        """测试窄端口不能直接实例化。"""
        with pytest.raises(TypeError):
            port()  # type: ignore[abstract]

    @pytest.mark.asyncio
    async def test_token_revocation_contract(self):
        """测试黑名单写入与校验的返回值语义。"""
        port = ConcreteTokenRevocation()
        assert await port.add_token_to_blacklist("token123", datetime(2030, 1, 1)) is True
        assert await port.is_token_blacklisted("token123") is False
        assert await port.blacklist_token_hash("hash1", datetime(2030, 1, 1)) is True
        assert port.blacklisted_hashes == ["hash1"]

    @pytest.mark.asyncio
    async def test_user_cache_contract(self):
        """测试用户信息/权限缓存的读写返回值语义。"""
        port = ConcreteUserCache()
        assert await port.get_user_permissions("user-1") is None
        assert await port.get_user_info("user-1") is None
        assert await port.set_user_permissions("user-1", []) is True
        assert await port.set_user_info("user-1", {"username": "admin"}) is True

    @pytest.mark.asyncio
    async def test_menu_cache_contract(self):
        """测试菜单全表缓存的读写与失效。"""
        port = ConcreteMenuCache()
        assert await port.get_all_menus() is None
        assert await port.set_all_menus([]) is True
        assert await port.invalidate_all_menus() is True

    @pytest.mark.asyncio
    async def test_dict_cache_contract(self):
        """测试字典缓存的读写与失效。"""
        port = ConcreteDictCache()
        assert await port.get_dict_items("gender") is None
        assert await port.set_dict_items("gender", []) is True
        assert await port.invalidate_dict("gender") is True

    @pytest.mark.asyncio
    async def test_online_session_store_contract(self):
        """测试在线会话端口的登记、列表与删除。"""
        port = ConcreteOnlineSessionStore()
        assert await port.set_online_user("h1", {"username": "admin"}, datetime(2030, 1, 1)) is True
        assert (await port.get_online_user("h1")) == {"username": "admin"}
        assert (await port.get_online_users()) == [{"username": "admin", "id": "h1"}]
        assert await port.delete_online_user("h1") is True
        assert await port.get_online_user("h1") is None


@pytest.mark.unit
class TestUserCacheBatchInvalidate:
    """UserCachePort 批量失效默认实现的退化语义。"""

    @pytest.mark.asyncio
    async def test_empty_list_is_success_without_calls(self):
        """空列表直接返回成功，不触发任何失效调用。"""
        port = ConcreteUserCache()
        assert await port.invalidate_users_batch([]) is True
        assert port.calls == []

    @pytest.mark.asyncio
    async def test_degrades_to_per_user_invalidation(self):
        """未重写批量方法时，退化为逐用户失效信息与权限。"""
        port = ConcreteUserCache()
        assert await port.invalidate_users_batch(["u1", "u2"]) is True
        assert port.calls == ["drop:info:u1", "drop:perms:u1", "drop:info:u2", "drop:perms:u2"]


@pytest.mark.unit
class TestCachePortAggregate:
    """聚合端口与窄端口的关系。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化聚合端口。"""
        with pytest.raises(TypeError):
            CachePort()  # type: ignore[abstract]

    def test_full_implementation_is_a_narrow_port(self):
        """测试实现聚合端口的对象同时是四个窄端口的实例（组合根本身可注入窄端口）。"""
        port = ConcreteCachePort()
        assert isinstance(port, CachePort)
        assert isinstance(port, TokenRevocationPort)
        assert isinstance(port, UserCachePort)
        assert isinstance(port, MenuCachePort)
        assert isinstance(port, DictCachePort)

    def test_online_session_store_is_not_in_aggregate(self):
        """测试在线会话独立于聚合端口：CachePort 不承载会话语义。"""
        assert not isinstance(ConcreteCachePort(), OnlineSessionStore)
        assert not isinstance(ConcreteOnlineSessionStore(), CachePort)


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
