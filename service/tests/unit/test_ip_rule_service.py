"""IP规则服务的单元测试。"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.services.ip_rule_service import IPRuleService, _parse_time_bound
from src.domain.entities.ip_rule import IPRuleEntity
from src.domain.exceptions import NotFoundError


@pytest.mark.unit
class TestParseTimeBound:
    """_parse_time_bound 辅助函数测试。"""

    def test_none(self):
        assert _parse_time_bound(None) is None

    def test_datetime_value(self):
        now = datetime.now()
        assert _parse_time_bound(now) == now

    def test_iso_string(self):
        result = _parse_time_bound("2024-01-15T10:30:00")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_z_suffix(self):
        result = _parse_time_bound("2024-01-15T10:30:00Z")
        assert result is not None
        assert result.year == 2024

    def test_empty_string(self):
        assert _parse_time_bound("") is None

    def test_whitespace_string(self):
        assert _parse_time_bound("   ") is None

    def test_invalid_string(self):
        assert _parse_time_bound("not-a-date") is None

    def test_other_type(self):
        assert _parse_time_bound(12345) is None


@pytest.mark.unit
class TestIPRuleService:
    """IPRuleService 测试类。"""

    @pytest.fixture
    def mock_ip_rule_repo(self):
        """创建模拟IP规则仓储。"""
        repo = AsyncMock()
        repo.get_ip_rules = AsyncMock(return_value=([], 0))
        repo.get_ip_rule_by_id = AsyncMock(return_value=None)
        repo.create_ip_rule = AsyncMock()
        repo.update_ip_rule = AsyncMock()
        repo.delete_ip_rules = AsyncMock(return_value=0)
        repo.clear_ip_rules = AsyncMock(return_value=0)
        return repo

    @pytest.fixture
    def ip_rule_service(self, mock_ip_rule_repo):
        """创建IP规则服务实例。"""
        return IPRuleService(ip_rule_repo=mock_ip_rule_repo)

    @pytest.mark.asyncio
    async def test_get_ip_rules(self, ip_rule_service, mock_ip_rule_repo):
        """测试获取IP规则列表。"""
        rule = IPRuleEntity(id="1", ip_address="1.1.1.1", rule_type="blacklist")
        mock_ip_rule_repo.get_ip_rules = AsyncMock(return_value=([rule], 1))

        rules, total = await ip_rule_service.get_ip_rules(page_num=1, page_size=10)
        assert total == 1
        assert len(rules) == 1

    @pytest.mark.asyncio
    async def test_get_ip_rules_with_time_range(self, ip_rule_service, mock_ip_rule_repo):
        """测试带时间范围获取IP规则。"""
        mock_ip_rule_repo.get_ip_rules = AsyncMock(return_value=([], 0))

        await ip_rule_service.get_ip_rules(
            page_num=1,
            page_size=10,
            created_time=["2024-01-01T00:00:00", "2024-12-31T23:59:59"],
        )
        call_kwargs = mock_ip_rule_repo.get_ip_rules.call_args[1]
        assert call_kwargs["start_time"] is not None
        assert call_kwargs["end_time"] is not None

    @pytest.mark.asyncio
    async def test_get_ip_rule_success(self, ip_rule_service, mock_ip_rule_repo):
        """测试获取单个IP规则。"""
        rule = IPRuleEntity(id="1", ip_address="1.1.1.1")
        mock_ip_rule_repo.get_ip_rule_by_id = AsyncMock(return_value=rule)

        result = await ip_rule_service.get_ip_rule("1")
        assert result.ip_address == "1.1.1.1"

    @pytest.mark.asyncio
    async def test_get_ip_rule_not_found(self, ip_rule_service, mock_ip_rule_repo):
        """测试获取不存在的IP规则。"""
        mock_ip_rule_repo.get_ip_rule_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await ip_rule_service.get_ip_rule("non-existent")

    @pytest.mark.asyncio
    async def test_create_ip_rule(self, ip_rule_service, mock_ip_rule_repo):
        """测试创建IP规则。"""
        created = IPRuleEntity(id="1", ip_address="1.1.1.1", rule_type="blacklist")
        mock_ip_rule_repo.create_ip_rule = AsyncMock(return_value=created)

        with patch.object(IPRuleService, "_refresh_ip_filter_cache", new_callable=AsyncMock):
            result = await ip_rule_service.create_ip_rule(ip_address="1.1.1.1", rule_type="blacklist")
        assert result.ip_address == "1.1.1.1"

    @pytest.mark.asyncio
    async def test_update_ip_rule_success(self, ip_rule_service, mock_ip_rule_repo):
        """测试更新IP规则。"""
        existing = IPRuleEntity(id="1", ip_address="1.1.1.1", rule_type="blacklist")
        mock_ip_rule_repo.get_ip_rule_by_id = AsyncMock(return_value=existing)
        mock_ip_rule_repo.update_ip_rule = AsyncMock(return_value=existing)

        with patch.object(IPRuleService, "_refresh_ip_filter_cache", new_callable=AsyncMock):
            await ip_rule_service.update_ip_rule(rule_id="1", ip_address="2.2.2.2")
        assert existing.ip_address == "2.2.2.2"

    @pytest.mark.asyncio
    async def test_update_ip_rule_not_found(self, ip_rule_service, mock_ip_rule_repo):
        """测试更新不存在的IP规则。"""
        mock_ip_rule_repo.get_ip_rule_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await ip_rule_service.update_ip_rule(rule_id="non-existent", ip_address="2.2.2.2")

    @pytest.mark.asyncio
    async def test_delete_ip_rules(self, ip_rule_service, mock_ip_rule_repo):
        """测试批量删除IP规则。"""
        mock_ip_rule_repo.delete_ip_rules = AsyncMock(return_value=2)
        with patch.object(IPRuleService, "_refresh_ip_filter_cache", new_callable=AsyncMock):
            result = await ip_rule_service.delete_ip_rules(["1", "2"])
        assert result == 2

    @pytest.mark.asyncio
    async def test_clear_ip_rules(self, ip_rule_service, mock_ip_rule_repo):
        """测试清空IP规则。"""
        mock_ip_rule_repo.clear_ip_rules = AsyncMock(return_value=5)
        with patch.object(IPRuleService, "_refresh_ip_filter_cache", new_callable=AsyncMock):
            result = await ip_rule_service.clear_ip_rules()
        assert result == 5

    @pytest.mark.asyncio
    async def test_get_ip_rules_with_filters(self, ip_rule_service, mock_ip_rule_repo):
        """测试带 rule_type 和 is_active 筛选获取 IP 规则。"""
        mock_ip_rule_repo.get_ip_rules = AsyncMock(return_value=([], 0))
        await ip_rule_service.get_ip_rules(page_num=1, page_size=10, rule_type="blacklist", is_active=1)
        call_kwargs = mock_ip_rule_repo.get_ip_rules.call_args[1]
        assert call_kwargs["rule_type"] == "blacklist"
        assert call_kwargs["is_active"] == 1

    @pytest.mark.asyncio
    async def test_get_ip_rules_with_single_time(self, ip_rule_service, mock_ip_rule_repo):
        """测试传入非列表时间值（业务逻辑覆盖）。"""
        mock_ip_rule_repo.get_ip_rules = AsyncMock(return_value=([], 0))
        await ip_rule_service.get_ip_rules(page_num=1, page_size=10, created_time="2024-01-01")
        call_kwargs = mock_ip_rule_repo.get_ip_rules.call_args[1]
        assert call_kwargs["start_time"] is None
        assert call_kwargs["end_time"] is None

    @pytest.mark.asyncio
    async def test_create_ip_rule_full_params(self, ip_rule_service, mock_ip_rule_repo):
        """测试创建IP规则所有参数。"""
        from datetime import datetime
        expires = datetime.now() + timedelta(days=7)
        created = IPRuleEntity(
            id="1",
            ip_address="10.0.0.1",
            rule_type="whitelist",
            reason="测试",
            is_active=1,
            expires_at=expires,
        )
        mock_ip_rule_repo.create_ip_rule = AsyncMock(return_value=created)

        with patch.object(IPRuleService, "_refresh_ip_filter_cache", new_callable=AsyncMock):
            result = await ip_rule_service.create_ip_rule(
                ip_address="10.0.0.1",
                rule_type="whitelist",
                reason="测试",
                is_active=1,
                expires_at=expires,
            )
        assert result.ip_address == "10.0.0.1"
        assert result.rule_type == "whitelist"
        assert result.reason == "测试"

    @pytest.mark.asyncio
    async def test_update_ip_rule_all_fields(self, ip_rule_service, mock_ip_rule_repo):
        """测试更新IP规则所有字段。"""
        existing = IPRuleEntity(id="1", ip_address="1.1.1.1", rule_type="blacklist")
        mock_ip_rule_repo.get_ip_rule_by_id = AsyncMock(return_value=existing)
        mock_ip_rule_repo.update_ip_rule = AsyncMock(return_value=existing)

        with patch.object(IPRuleService, "_refresh_ip_filter_cache", new_callable=AsyncMock):
            await ip_rule_service.update_ip_rule(
                rule_id="1",
                ip_address="2.2.2.2",
                rule_type="whitelist",
                reason="更新",
                is_active=0,
                description="新描述",
            )
        assert existing.ip_address == "2.2.2.2"
        assert existing.rule_type == "whitelist"
        assert existing.reason == "更新"
        assert existing.is_active == 0
        assert existing.description == "新描述"

    @pytest.mark.asyncio
    async def test_delete_ip_rules_empty(self, ip_rule_service, mock_ip_rule_repo):
        """测试批量删除空列表。"""
        mock_ip_rule_repo.delete_ip_rules = AsyncMock(return_value=0)
        with patch.object(IPRuleService, "_refresh_ip_filter_cache", new_callable=AsyncMock):
            result = await ip_rule_service.delete_ip_rules([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_refresh_cache_with_filter_port(self, ip_rule_service, mock_ip_rule_repo):
        """测试 _refresh_ip_filter_cache 有 filter_port。"""
        filter_port = AsyncMock()
        filter_port.refresh = AsyncMock()
        service = IPRuleService(ip_rule_repo=mock_ip_rule_repo, ip_filter_port=filter_port)
        with patch.object(service, "_refresh_ip_filter_cache", new_callable=AsyncMock) as mock_refresh:
            await service.create_ip_rule(ip_address="1.1.1.1", rule_type="blacklist")
            mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_cache_error_logged(self, mock_ip_rule_repo):
        """测试缓存刷新失败时调用 logging_port。"""
        filter_port = AsyncMock()
        filter_port.refresh = AsyncMock(side_effect=Exception("Cache error"))
        logger = MagicMock()
        service = IPRuleService(ip_rule_repo=mock_ip_rule_repo, ip_filter_port=filter_port, logging_port=logger)
        await service._refresh_ip_filter_cache()
        logger.warning.assert_called_once_with("刷新 IP 过滤缓存失败", exc_info=True)

    @pytest.mark.asyncio
    async def test_refresh_cache_no_filter_port(self, ip_rule_service):
        """测试 _refresh_ip_filter_cache 无 filter_port。"""
        # Should not raise any error
        await ip_rule_service._refresh_ip_filter_cache()
