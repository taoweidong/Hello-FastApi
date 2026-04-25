"""系统配置仓储接口的单元测试。

测试 SystemConfigRepositoryInterface 抽象基类的方法签名和返回类型。
"""

import pytest

from src.domain.entities.system_config import SystemConfigEntity
from src.domain.repositories.system_config_repository import SystemConfigRepositoryInterface


class ConcreteSystemConfigRepository(SystemConfigRepositoryInterface):
    """用于测试的 SystemConfigRepositoryInterface 最小化具体实现。"""

    def __init__(self, session=None):
        self.session = session

    async def get_all(
        self, page_num: int = 1, page_size: int = 10, key: str | None = None, is_active: int | None = None
    ) -> list[SystemConfigEntity]:
        return []

    async def count(self, key: str | None = None, is_active: int | None = None) -> int:
        return 0

    async def get_by_id(self, config_id: str) -> SystemConfigEntity | None:
        return None

    async def get_by_key(self, key: str) -> SystemConfigEntity | None:
        return None

    async def create(self, config: SystemConfigEntity) -> SystemConfigEntity:
        return config

    async def update(self, config: SystemConfigEntity) -> SystemConfigEntity:
        return config

    async def delete(self, config_id: str) -> bool:
        return True


@pytest.mark.unit
class TestSystemConfigRepositoryInterface:
    """SystemConfigRepositoryInterface 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            SystemConfigRepositoryInterface(session=None)  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        repo = ConcreteSystemConfigRepository()
        assert repo is not None
        assert isinstance(repo, SystemConfigRepositoryInterface)

    # ---- get_all ----

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        """测试 get_all 返回列表。"""
        repo = ConcreteSystemConfigRepository()
        result = await repo.get_all()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_all_with_all_params(self):
        """测试 get_all 接受所有可选参数。"""
        repo = ConcreteSystemConfigRepository()
        result = await repo.get_all(page_num=1, page_size=20, key="site_name", is_active=1)
        assert isinstance(result, list)

    # ---- count ----

    @pytest.mark.asyncio
    async def test_count_returns_int(self):
        """测试 count 返回整数。"""
        repo = ConcreteSystemConfigRepository()
        result = await repo.count()
        assert isinstance(result, int)

    @pytest.mark.asyncio
    async def test_count_with_all_params(self):
        """测试 count 接受所有可选参数。"""
        repo = ConcreteSystemConfigRepository()
        result = await repo.count(key="site_name", is_active=1)
        assert isinstance(result, int)

    # ---- get_by_id ----

    @pytest.mark.asyncio
    async def test_get_by_id_accepts_str(self):
        """测试 get_by_id 接受字符串参数。"""
        repo = ConcreteSystemConfigRepository()
        result = await repo.get_by_id("config-1")
        assert result is None

    # ---- get_by_key ----

    @pytest.mark.asyncio
    async def test_get_by_key_accepts_str(self):
        """测试 get_by_key 接受字符串参数。"""
        repo = ConcreteSystemConfigRepository()
        result = await repo.get_by_key("site_name")
        assert result is None

    # ---- create ----

    @pytest.mark.asyncio
    async def test_create_returns_system_config_entity(self):
        """测试 create 返回系统配置实体。"""
        repo = ConcreteSystemConfigRepository()
        entity = SystemConfigEntity(id="config-1", key="site_name", value='"My Site"')
        result = await repo.create(entity)
        assert isinstance(result, SystemConfigEntity)

    # ---- update ----

    @pytest.mark.asyncio
    async def test_update_returns_system_config_entity(self):
        """测试 update 返回系统配置实体。"""
        repo = ConcreteSystemConfigRepository()
        entity = SystemConfigEntity(id="config-1", key="site_name", value='"My Site"')
        result = await repo.update(entity)
        assert isinstance(result, SystemConfigEntity)

    # ---- delete ----

    @pytest.mark.asyncio
    async def test_delete_returns_bool(self):
        """测试 delete 返回布尔值。"""
        repo = ConcreteSystemConfigRepository()
        result = await repo.delete("config-1")
        assert isinstance(result, bool)
