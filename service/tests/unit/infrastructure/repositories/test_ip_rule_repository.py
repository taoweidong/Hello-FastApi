"""IPRuleRepository 单元测试。"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.ip_rule import IPRuleEntity
from src.infrastructure.repositories.ip_rule_repository import IPRuleRepository


@pytest.mark.unit
class TestIPRuleRepository:
    """IPRuleRepository 测试类。"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return IPRuleRepository(mock_session)

    def test_init(self, repo, mock_session):
        """测试初始化设置 session 和 crud。"""
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_ip_rules_default(self, repo, mock_session):
        """测试 get_ip_rules 默认分页。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.to_domain.return_value = IPRuleEntity(id="1", ip_address="192.168.1.1")
        mock_result.all.return_value = [mock_model]
        mock_count_result = MagicMock()
        mock_count_result.one.return_value = 1
        mock_session.exec = AsyncMock(side_effect=[mock_result, mock_count_result])

        rules, total = await repo.get_ip_rules()

        assert len(rules) == 1
        assert total == 1
        assert rules[0].ip_address == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_get_ip_rules_with_filters(self, repo, mock_session):
        """测试 get_ip_rules 带筛选条件。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count_result = MagicMock()
        mock_count_result.one.return_value = 0
        mock_session.exec.return_value = mock_count_result

        rules, total = await repo.get_ip_rules(
            page_num=1,
            page_size=20,
            rule_type="blacklist",
            is_active=1,
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 12, 31),
        )

        assert rules == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_ip_rule_by_id_found(self, repo):
        """测试 get_ip_rule_by_id 找到规则。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = IPRuleEntity(id="1", ip_address="10.0.0.1")
        repo._crud.get = AsyncMock(return_value=mock_model)

        result = await repo.get_ip_rule_by_id("1")

        assert result is not None
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_get_ip_rule_by_id_not_found(self, repo):
        """测试 get_ip_rule_by_id 未找到返回 None。"""
        repo._crud.get = AsyncMock(return_value=None)

        result = await repo.get_ip_rule_by_id("not-exist")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_ip_rule(self, repo, mock_session):
        """测试 create_ip_rule 创建规则。"""
        entity = IPRuleEntity(id="1", ip_address="10.0.0.1", rule_type="blacklist")
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity
        repo.get_ip_rule_by_id = AsyncMock(return_value=entity)

        with patch("src.infrastructure.repositories.ip_rule_repository.IPRule.from_domain", return_value=mock_model):
            result = await repo.create_ip_rule(entity)

        assert result is not None
        assert result.id == "1"
        mock_session.add.assert_called_once_with(mock_model)

    @pytest.mark.asyncio
    async def test_update_ip_rule(self, repo, mock_session):
        """测试 update_ip_rule 更新规则。"""
        entity = IPRuleEntity(
            id="1",
            ip_address="10.0.0.2",
            rule_type="whitelist",
            reason="更新",
            is_active=1,
            creator_id="u1",
            modifier_id="u2",
            expires_at=None,
            description="desc",
        )
        repo.get_ip_rule_by_id = AsyncMock(return_value=entity)

        result = await repo.update_ip_rule(entity)

        assert result is not None
        assert result.ip_address == "10.0.0.2"

    @pytest.mark.asyncio
    async def test_delete_ip_rules_success(self, repo, mock_session):
        """测试 delete_ip_rules 批量删除成功。"""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.exec.return_value = mock_result

        count = await repo.delete_ip_rules(["1", "2", "3"])

        assert count == 3

    @pytest.mark.asyncio
    async def test_delete_ip_rules_empty(self, repo):
        """测试 delete_ip_rules 空列表返回 0。"""
        count = await repo.delete_ip_rules([])

        assert count == 0

    @pytest.mark.asyncio
    async def test_clear_ip_rules(self, repo, mock_session):
        """测试 clear_ip_rules 清空所有规则。"""
        mock_count = MagicMock()
        mock_count.one.return_value = 5
        mock_session.exec.return_value = mock_count

        total = await repo.clear_ip_rules()

        assert total == 5

    @pytest.mark.asyncio
    async def test_get_effective_ip_rules(self, repo, mock_session):
        """测试 get_effective_ip_rules 获取生效规则。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.to_domain.return_value = IPRuleEntity(
            id="1", ip_address="10.0.0.1", rule_type="blacklist", is_active=1
        )
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        rules = await repo.get_effective_ip_rules()

        assert len(rules) == 1
        assert rules[0].is_effective is True

    @pytest.mark.asyncio
    async def test_get_effective_ip_rules_empty(self, repo, mock_session):
        """测试 get_effective_ip_rules 无生效规则。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        rules = await repo.get_effective_ip_rules()

        assert rules == []

    @pytest.mark.asyncio
    async def test_get_ip_rules_rule_type_only(self, repo, mock_session):
        """测试 get_ip_rules 仅按类型筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.one.return_value = 0
        mock_session.exec.return_value = mock_count

        rules, total = await repo.get_ip_rules(rule_type="whitelist")

        assert rules == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_ip_rules_is_active_only(self, repo, mock_session):
        """测试 get_ip_rules 仅按启用状态筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.one.return_value = 0
        mock_session.exec.return_value = mock_count

        rules, total = await repo.get_ip_rules(is_active=1)

        assert rules == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_ip_rules_start_time_only(self, repo, mock_session):
        """测试 get_ip_rules 仅按开始时间筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.one.return_value = 0
        mock_session.exec.return_value = mock_count

        rules, total = await repo.get_ip_rules(start_time=datetime(2024, 1, 1))

        assert rules == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_ip_rules_end_time_only(self, repo, mock_session):
        """测试 get_ip_rules 仅按结束时间筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_count = MagicMock()
        mock_count.one.return_value = 0
        mock_session.exec.return_value = mock_count

        rules, total = await repo.get_ip_rules(end_time=datetime(2024, 12, 31))

        assert rules == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_delete_ip_rules_not_found(self, repo, mock_session):
        """测试 delete_ip_rules 未找到返回 0。"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.exec.return_value = mock_result

        count = await repo.delete_ip_rules(["nonexistent"])

        assert count == 0

    @pytest.mark.asyncio
    async def test_clear_ip_rules_empty(self, repo, mock_session):
        """测试 clear_ip_rules 空表返回 0。"""
        mock_count = MagicMock()
        mock_count.one.return_value = 0
        mock_session.exec.return_value = mock_count

        total = await repo.clear_ip_rules()

        assert total == 0
