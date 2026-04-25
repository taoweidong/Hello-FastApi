"""IP 规则仓储接口的单元测试。

测试 IPRuleRepositoryInterface 抽象基类的方法签名和返回类型。
"""

from datetime import datetime

import pytest

from src.domain.entities.ip_rule import IPRuleEntity
from src.domain.repositories.ip_rule_repository import IPRuleRepositoryInterface


class ConcreteIPRuleRepository(IPRuleRepositoryInterface):
    """用于测试的 IPRuleRepositoryInterface 最小化具体实现。"""

    def __init__(self, session=None):
        self.session = session

    async def get_ip_rules(
        self,
        page_num: int = 1,
        page_size: int = 10,
        rule_type: str | None = None,
        is_active: int | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> tuple[list[IPRuleEntity], int]:
        return ([], 0)

    async def get_ip_rule_by_id(self, rule_id: str) -> IPRuleEntity | None:
        return None

    async def create_ip_rule(self, rule: IPRuleEntity) -> IPRuleEntity:
        return rule

    async def update_ip_rule(self, rule: IPRuleEntity) -> IPRuleEntity:
        return rule

    async def delete_ip_rules(self, rule_ids: list[str]) -> int:
        return len(rule_ids)

    async def clear_ip_rules(self) -> int:
        return 0

    async def get_effective_ip_rules(self) -> list[IPRuleEntity]:
        return []


@pytest.mark.unit
class TestIPRuleRepositoryInterface:
    """IPRuleRepositoryInterface 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            IPRuleRepositoryInterface(session=None)  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        repo = ConcreteIPRuleRepository()
        assert repo is not None
        assert isinstance(repo, IPRuleRepositoryInterface)

    # ---- get_ip_rules ----

    @pytest.mark.asyncio
    async def test_get_ip_rules_returns_tuple(self):
        """测试 get_ip_rules 返回元组。"""
        repo = ConcreteIPRuleRepository()
        result = await repo.get_ip_rules()
        assert isinstance(result, tuple)
        assert len(result) == 2
        rules, total = result
        assert isinstance(rules, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_get_ip_rules_with_all_params(self):
        """测试 get_ip_rules 接受所有可选参数。"""
        repo = ConcreteIPRuleRepository()
        result = await repo.get_ip_rules(
            page_num=1,
            page_size=20,
            rule_type="black",
            is_active=1,
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 12, 31),
        )
        assert isinstance(result, tuple)
        assert len(result) == 2

    # ---- get_ip_rule_by_id ----

    @pytest.mark.asyncio
    async def test_get_ip_rule_by_id_accepts_str(self):
        """测试 get_ip_rule_by_id 接受字符串参数。"""
        repo = ConcreteIPRuleRepository()
        result = await repo.get_ip_rule_by_id("rule-1")
        assert result is None

    # ---- create_ip_rule ----

    @pytest.mark.asyncio
    async def test_create_ip_rule_returns_entity(self):
        """测试 create_ip_rule 返回 IP 规则实体。"""
        repo = ConcreteIPRuleRepository()
        entity = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist")
        result = await repo.create_ip_rule(entity)
        assert isinstance(result, IPRuleEntity)

    # ---- update_ip_rule ----

    @pytest.mark.asyncio
    async def test_update_ip_rule_returns_entity(self):
        """测试 update_ip_rule 返回 IP 规则实体。"""
        repo = ConcreteIPRuleRepository()
        entity = IPRuleEntity(id="rule-1", ip_address="192.168.1.1", rule_type="blacklist")
        result = await repo.update_ip_rule(entity)
        assert isinstance(result, IPRuleEntity)

    # ---- delete_ip_rules ----

    @pytest.mark.asyncio
    async def test_delete_ip_rules_returns_int(self):
        """测试 delete_ip_rules 返回整数。"""
        repo = ConcreteIPRuleRepository()
        result = await repo.delete_ip_rules(["rule-1", "rule-2"])
        assert isinstance(result, int)
        assert result == 2

    # ---- clear_ip_rules ----

    @pytest.mark.asyncio
    async def test_clear_ip_rules_returns_int(self):
        """测试 clear_ip_rules 返回整数。"""
        repo = ConcreteIPRuleRepository()
        result = await repo.clear_ip_rules()
        assert isinstance(result, int)

    # ---- get_effective_ip_rules ----

    @pytest.mark.asyncio
    async def test_get_effective_ip_rules_returns_list(self):
        """测试 get_effective_ip_rules 返回列表。"""
        repo = ConcreteIPRuleRepository()
        result = await repo.get_effective_ip_rules()
        assert isinstance(result, list)
