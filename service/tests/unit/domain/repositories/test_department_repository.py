"""部门仓储接口的单元测试。

测试 DepartmentRepositoryInterface 抽象基类的方法签名和返回类型。
"""


import pytest

from src.domain.entities.department import DepartmentEntity
from src.domain.repositories.department_repository import DepartmentRepositoryInterface


class ConcreteDepartmentRepository(DepartmentRepositoryInterface):
    """用于测试的 DepartmentRepositoryInterface 最小化具体实现。"""

    def __init__(self, session=None):
        self.session = session

    async def get_all(self) -> list[DepartmentEntity]:
        return []

    async def get_by_id(self, dept_id: str) -> DepartmentEntity | None:
        return None

    async def get_by_name(self, name: str) -> DepartmentEntity | None:
        return None

    async def get_by_code(self, code: str) -> DepartmentEntity | None:
        return None

    async def get_by_parent_id(self, parent_id: str | None) -> list[DepartmentEntity]:
        return []

    async def create(self, department: DepartmentEntity) -> DepartmentEntity:
        return department

    async def update(self, department: DepartmentEntity) -> DepartmentEntity:
        return department

    async def delete(self, dept_id: str) -> bool:
        return True

    async def count(self, name: str | None = None, is_active: int | None = None) -> int:
        return 0

    async def get_filtered(self, name: str | None = None, is_active: int | None = None) -> list[DepartmentEntity]:
        return []


@pytest.mark.unit
class TestDepartmentRepositoryInterface:
    """DepartmentRepositoryInterface 抽象基类测试。"""

    def test_cannot_instantiate_abc_directly(self):
        """测试不能直接实例化抽象基类。"""
        with pytest.raises(TypeError):
            DepartmentRepositoryInterface(session=None)  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self):
        """测试具体子类可以实例化。"""
        repo = ConcreteDepartmentRepository()
        assert repo is not None
        assert isinstance(repo, DepartmentRepositoryInterface)

    # ---- get_all ----

    @pytest.mark.asyncio
    async def test_get_all_returns_list(self):
        """测试 get_all 返回列表。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.get_all()
        assert isinstance(result, list)

    # ---- get_by_id ----

    @pytest.mark.asyncio
    async def test_get_by_id_accepts_str(self):
        """测试 get_by_id 接受字符串参数。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.get_by_id("dept-1")
        assert result is None

    # ---- get_by_name ----

    @pytest.mark.asyncio
    async def test_get_by_name_accepts_str(self):
        """测试 get_by_name 接受字符串参数。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.get_by_name("技术部")
        assert result is None

    # ---- get_by_code ----

    @pytest.mark.asyncio
    async def test_get_by_code_accepts_str(self):
        """测试 get_by_code 接受字符串参数。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.get_by_code("tech")
        assert result is None

    # ---- get_by_parent_id ----

    @pytest.mark.asyncio
    async def test_get_by_parent_id_accepts_str_or_none(self):
        """测试 get_by_parent_id 接受字符串或 None。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.get_by_parent_id("parent-1")
        assert isinstance(result, list)
        result_none = await repo.get_by_parent_id(None)
        assert isinstance(result_none, list)

    # ---- create ----

    @pytest.mark.asyncio
    async def test_create_returns_department_entity(self):
        """测试 create 返回部门实体。"""
        repo = ConcreteDepartmentRepository()
        entity = DepartmentEntity(id="dept-1", name="技术部", code="tech")
        result = await repo.create(entity)
        assert isinstance(result, DepartmentEntity)
        assert result.id == "dept-1"

    # ---- update ----

    @pytest.mark.asyncio
    async def test_update_returns_department_entity(self):
        """测试 update 返回部门实体。"""
        repo = ConcreteDepartmentRepository()
        entity = DepartmentEntity(id="dept-1", name="技术部", code="tech")
        result = await repo.update(entity)
        assert isinstance(result, DepartmentEntity)

    # ---- delete ----

    @pytest.mark.asyncio
    async def test_delete_returns_bool(self):
        """测试 delete 返回布尔值。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.delete("dept-1")
        assert isinstance(result, bool)

    # ---- count ----

    @pytest.mark.asyncio
    async def test_count_returns_int(self):
        """测试 count 返回整数。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.count()
        assert isinstance(result, int)

    # ---- get_filtered ----

    @pytest.mark.asyncio
    async def test_get_filtered_returns_list(self):
        """测试 get_filtered 返回列表。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.get_filtered(name="技术")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_filtered_with_all_params(self):
        """测试 get_filtered 接受所有可选参数。"""
        repo = ConcreteDepartmentRepository()
        result = await repo.get_filtered(name="技术", is_active=1)
        assert isinstance(result, list)
