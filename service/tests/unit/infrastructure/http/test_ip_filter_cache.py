"""IPFilterCache 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.ip_rule import IPRuleEntity
from src.infrastructure.http.ip_filter_cache import IPFilterCache, get_ip_filter_cache


@pytest.mark.unit
class TestIPFilterCache:
    """IPFilterCache 测试类。"""

    @pytest.fixture
    def cache(self):
        return IPFilterCache()

    def test_init(self, cache):
        """测试初始化后 app 和 cache_service 为 None。"""
        assert cache._app is None
        assert cache._cache_service is None

    def test_set_app(self, cache):
        """测试 set_app 设置 app 引用。"""
        mock_app = MagicMock()
        cache.set_app(mock_app)
        assert cache._app is mock_app

    def test_get_ip_filter_cache_returns_singleton(self):
        """测试 get_ip_filter_cache 返回单例。"""
        c1 = get_ip_filter_cache()
        c2 = get_ip_filter_cache()
        assert c1 is c2

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_db")
    @patch("src.infrastructure.repositories.ip_rule_repository.IPRuleRepository")
    @patch("src.infrastructure.http.ip_filter_cache.CacheService")
    async def test_load_to_app_state_success(self, mock_cache_cls, mock_repo_cls, mock_get_db, cache):
        """测试 load_to_app_state 成功加载规则到 app.state。"""
        mock_app = MagicMock()
        mock_session = AsyncMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_session]

        mock_repo = MagicMock()
        mock_repo.get_effective_ip_rules = AsyncMock(
            return_value=[
                IPRuleEntity(id="1", ip_address="192.168.1.1", rule_type=IPRuleEntity.BLACKLIST),
                IPRuleEntity(id="2", ip_address="10.0.0.1", rule_type=IPRuleEntity.WHITELIST),
            ]
        )
        mock_repo_cls.return_value = mock_repo

        mock_cache = MagicMock()
        mock_cache.set_ip_rules = AsyncMock()
        mock_cache_cls.return_value = mock_cache

        await cache.load_to_app_state(mock_app)

        assert mock_app.state.ip_blacklist == {"192.168.1.1"}
        assert mock_app.state.ip_whitelist == {"10.0.0.1"}
        mock_cache.set_ip_rules.assert_called_once_with({"192.168.1.1"}, {"10.0.0.1"})

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_db")
    async def test_load_to_app_state_db_error(self, mock_get_db, cache):
        """测试 load_to_app_state 数据库异常时以空规则启动。"""
        mock_app = MagicMock()
        mock_get_db.side_effect = Exception("数据库连接失败")

        await cache.load_to_app_state(mock_app)

        assert mock_app.state.ip_blacklist == set()
        assert mock_app.state.ip_whitelist == set()

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_db")
    @patch("src.infrastructure.repositories.ip_rule_repository.IPRuleRepository")
    async def test_refresh_without_app_skips(self, mock_repo_cls, mock_get_db, cache):
        """测试 refresh 在 app 未设置时跳过。"""
        assert cache._app is None
        await cache.refresh()
        mock_get_db.assert_not_called()

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_db")
    @patch("src.infrastructure.repositories.ip_rule_repository.IPRuleRepository")
    @patch("src.infrastructure.http.ip_filter_cache.CacheService")
    async def test_refresh_success(self, mock_cache_cls, mock_repo_cls, mock_get_db, cache):
        """测试 refresh 成功刷新缓存。"""
        mock_app = MagicMock()
        cache._app = mock_app
        mock_session = AsyncMock()
        mock_get_db.return_value.__aiter__.return_value = [mock_session]

        mock_repo = MagicMock()
        mock_repo.get_effective_ip_rules = AsyncMock(return_value=[])
        mock_repo_cls.return_value = mock_repo

        mock_cache = MagicMock()
        mock_cache.set_ip_rules = AsyncMock()
        mock_cache_cls.return_value = mock_cache

        await cache.refresh()

        assert mock_app.state.ip_blacklist == set()
        assert mock_app.state.ip_whitelist == set()
        mock_cache.set_ip_rules.assert_called_once()

    def test_classify_rules(self, cache):
        """测试 _classify_rules 正确分类黑白名单。"""
        rules = [
            IPRuleEntity(id="1", ip_address="192.168.1.1", rule_type="blacklist"),
            IPRuleEntity(id="2", ip_address="10.0.0.1", rule_type="whitelist"),
            IPRuleEntity(id="3", ip_address="192.168.1.2", rule_type="blacklist"),
        ]
        blacklist, whitelist = cache._classify_rules(rules)
        assert blacklist == {"192.168.1.1", "192.168.1.2"}
        assert whitelist == {"10.0.0.1"}

    def test_classify_rules_empty(self, cache):
        """测试 _classify_rules 处理空列表。"""
        blacklist, whitelist = cache._classify_rules([])
        assert blacklist == set()
        assert whitelist == set()

    def test_classify_rules_unknown_type_ignored(self, cache):
        """测试 _classify_rules 忽略未知类型。"""
        rules = [IPRuleEntity(id="1", ip_address="192.168.1.1", rule_type="unknown")]
        blacklist, whitelist = cache._classify_rules(rules)
        assert blacklist == set()
        assert whitelist == set()

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.CacheService")
    async def test_ensure_cache_service_creates_service(self, mock_cache_cls, cache):
        """测试 _ensure_cache_service 创建 CacheService。"""
        mock_cache_cls.return_value = MagicMock()
        svc = cache._ensure_cache_service()
        assert svc is not None
        assert cache._cache_service is svc

    @pytest.mark.asyncio
    async def test_ensure_cache_service_return_cached(self, cache):
        """测试 _ensure_cache_service 返回已缓存的实例。"""
        mock_svc = MagicMock()
        cache._cache_service = mock_svc
        svc = cache._ensure_cache_service()
        assert svc is mock_svc


@pytest.mark.unit
class TestIPFilterCacheEdgeCases:
    """IPFilterCache 额外路径测试。"""

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_redis")
    @patch("src.infrastructure.http.ip_filter_cache.CacheService")
    async def test_get_cache_service_async_creates(self, mock_cache_cls, mock_get_redis):
        """测试 _get_cache_service 创建新实例。"""
        cache = IPFilterCache()
        assert cache._cache_service is None
        mock_get_redis.return_value = MagicMock()
        mock_cache_cls.return_value = MagicMock()

        svc = await cache._get_cache_service()
        assert svc is not None
        assert cache._cache_service is svc

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_redis")
    async def test_get_cache_service_async_redis_error(self, mock_get_redis):
        """测试 _get_cache_service 在 Redis 不可用时降级。"""
        cache = IPFilterCache()
        mock_get_redis.side_effect = Exception("Redis 不可用")

        svc = await cache._get_cache_service()
        assert svc is not None
        assert cache._cache_service is not None

    @pytest.mark.asyncio
    async def test_get_cache_service_async_cached(self):
        """测试 _get_cache_service 返回已缓存的实例。"""
        cache = IPFilterCache()
        mock_svc = MagicMock()
        cache._cache_service = mock_svc

        svc = await cache._get_cache_service()
        assert svc is mock_svc

    @pytest.mark.asyncio
    @patch("src.infrastructure.http.ip_filter_cache.get_db")
    async def test_refresh_db_error_silent(self, mock_get_db):
        """测试 refresh 数据库异常时静默处理。"""
        cache = IPFilterCache()
        cache._app = MagicMock()
        mock_get_db.side_effect = Exception("数据库错误")

        await cache.refresh()  # should not raise
