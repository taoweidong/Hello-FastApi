"""字典仓储接口的单元测试。

测试 DictionaryRepositoryInterface 抽象基类的方法签名和返回类型。
"""

import pytest

from src.domain.entities.dictionary import DictionaryEntity
from src.domain.repositories.dictionary_repository import DictionaryRepositoryInterface


class ConcreteDictionaryRepository(DictionaryRepositoryInterface):
    """用于测试的 DictionaryRepositoryInterface 最小化具体实现。"""

    def __init__(self, session=None):
        self.session = session

    async def get_all(self) -> list[DictionaryEntity]:
        return []

    async def get_by_id(self, dict_id: str) -> DictionaryEntity | None:
        return None

    async def get_by_name(self, name: str) -> DictionaryEntity | None:
        return None

    async def get_by_parent_id(self, parent_id: str | None) -> list[DictionaryEntity]:
        return []

    async def get_max_sort(self, parent_id: str | None) -> int:
        return 0

    async def create(self, dictionary: DictionaryEntity) -> DictionaryEntity:
        return dictionary

    async def update(self, dictionary: DictionaryEntity) -> DictionaryEntity:
        return dictionary

    async def delete(self, dict_id: str) -> bool:
        return True

    async def get_filtered(self, name: str | None = None, is_active: int | None = None) -> list[DictionaryEntity]:
        return []


@pytest.mark.unit
class TestDictionaryRepositoryInterface:
    """DictionaryRepositoryInterface 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            DictionaryRepositoryInterface(session=None)  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        repo = ConcreteDictionaryRepository()
        assert repo is not None
        assert isinstance(repo, DictionaryRepositoryInterface)

    # ---- get_all ----

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        """测试 get_all 返回列表。"""
        repo = ConcreteDictionaryRepository()
        result = await repo.get_all()
        assert isinstance(result, list)

    # ---- get_by_id ----

    @pytest.mark.asyncio
    async def test_get_by_id_accepts_str(self):
        """测试 get_by_id 接受字符串参数。"""
        repo = ConcreteDictionaryRepository()
        result = await repo.get_by_id("dict-1")
        assert result is None

    # ---- get_by_name ----

    @pytest.mark.asyncio
    async def test_get_by_name_accepts_str(self):
        """测试 get_by_name 接受字符串参数。"""
        repo = ConcreteDictionaryRepository()
        result = await repo.get_by_name("性别")
        assert result is None

    # ---- get_by_parent_id ----

    @pytest.mark.asyncio
    async def test_get_by_parent_id_accepts_str_or_none(self):
        """测试 get_by_parent_id 接受字符串或 None。"""
        repo = ConcreteDictionaryRepository()
        result = await repo.get_by_parent_id("parent-1")
        assert isinstance(result, list)
        result_none = await repo.get_by_parent_id(None)
        assert isinstance(result_none, list)

    # ---- get_max_sort ----

    @pytest.mark.asyncio
    async def test_get_max_sort_returns_int(self):
        """测试 get_max_sort 返回整数。"""
        repo = ConcreteDictionaryRepository()
        result = await repo.get_max_sort(None)
        assert isinstance(result, int)

    # ---- create ----

    @pytest.mark.asyncio
    async def test_create_returns_dictionary_entity(self):
        """测试 create 返回字典实体。"""
        repo = ConcreteDictionaryRepository()
        entity = DictionaryEntity(id="dict-1", name="性别", sort=0)
        result = await repo.create(entity)
        assert isinstance(result, DictionaryEntity)

    # ---- update ----

    @pytest.mark.asyncio
    async def test_update_returns_dictionary_entity(self):
        """测试 update 返回字典实体。"""
        repo = ConcreteDictionaryRepository()
        entity = DictionaryEntity(id="dict-1", name="性别", sort=0)
        result = await repo.update(entity)
        assert isinstance(result, DictionaryEntity)

    # ---- delete ----

    @pytest.mark.asyncio
    async def test_delete_returns_bool(self):
        """测试 delete 返回布尔值。"""
        repo = ConcreteDictionaryRepository()
        result = await repo.delete("dict-1")
        assert isinstance(result, bool)

    # ---- get_filtered ----

    @pytest.mark.asyncio
    async def test_get_filtered_returns_list(self):
        """测试 get_filtered 返回列表。"""
        repo = ConcreteDictionaryRepository()
        result = await repo.get_filtered(name="性别")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_filtered_with_all_params(self):
        """测试 get_filtered 接受所有可选参数。"""
        repo = ConcreteDictionaryRepository()
        result = await repo.get_filtered(name="性别", is_active=1)
        assert isinstance(result, list)
