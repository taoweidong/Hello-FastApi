"""部门服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.department_dto import DepartmentCreateDTO, DepartmentListQueryDTO, DepartmentUpdateDTO
from src.application.services.department_service import DepartmentService
from src.domain.entities.department import DepartmentEntity
from src.domain.exceptions import BusinessError, ConflictError, NotFoundError


@pytest.mark.unit
class TestDepartmentService:
    """DepartmentService 测试类。"""

    @pytest.fixture
    def mock_dept_repo(self):
        """创建模拟部门仓储。"""
        repo = AsyncMock()
        repo.get_all = AsyncMock(return_value=[])
        repo.get_filtered = AsyncMock(return_value=[])
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_by_name = AsyncMock(return_value=None)
        repo.get_by_code = AsyncMock(return_value=None)
        repo.get_by_parent_id = AsyncMock(return_value=[])
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def dept_service(self, mock_dept_repo):
        """创建部门服务实例。"""
        return DepartmentService(dept_repo=mock_dept_repo)

    @pytest.mark.asyncio
    async def test_get_departments_empty(self, dept_service, mock_dept_repo):
        """测试获取空部门列表。"""
        mock_dept_repo.get_filtered = AsyncMock(return_value=[])
        query = DepartmentListQueryDTO()
        result = await dept_service.get_departments(query)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_departments_with_name_filter(self, dept_service, mock_dept_repo):
        """测试按名称筛选部门。"""
        d1 = DepartmentEntity(id="1", name="技术部")
        mock_dept_repo.get_filtered = AsyncMock(return_value=[d1])
        query = DepartmentListQueryDTO(name="技术")
        result = await dept_service.get_departments(query)
        assert len(result) == 1
        assert result[0].name == "技术部"

    @pytest.mark.asyncio
    async def test_create_department_success(self, dept_service, mock_dept_repo):
        """测试创建部门成功。"""
        mock_dept_repo.get_by_name = AsyncMock(return_value=None)
        mock_dept_repo.get_by_code = AsyncMock(return_value=None)
        created = DepartmentEntity(id="1", name="技术部", code="tech")
        mock_dept_repo.create = AsyncMock(return_value=created)

        dto = DepartmentCreateDTO(name="技术部", code="tech", isActive=1)
        result = await dept_service.create_department(dto)
        assert result.name == "技术部"

    @pytest.mark.asyncio
    async def test_create_department_duplicate_name(self, dept_service, mock_dept_repo):
        """测试创建部门时名称重复。"""
        existing = DepartmentEntity(id="1", name="技术部")
        mock_dept_repo.get_by_name = AsyncMock(return_value=existing)

        dto = DepartmentCreateDTO(name="技术部", code="tech2", isActive=1)
        with pytest.raises(ConflictError) as exc_info:
            await dept_service.create_department(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_department_duplicate_code(self, dept_service, mock_dept_repo):
        """测试创建部门时编码重复。"""
        mock_dept_repo.get_by_name = AsyncMock(return_value=None)
        existing = DepartmentEntity(id="1", code="tech")
        mock_dept_repo.get_by_code = AsyncMock(return_value=existing)

        dto = DepartmentCreateDTO(name="新部门", code="tech", isActive=1)
        with pytest.raises(ConflictError) as exc_info:
            await dept_service.create_department(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_department_parent_not_found(self, dept_service, mock_dept_repo):
        """测试创建部门时父部门不存在。"""
        mock_dept_repo.get_by_name = AsyncMock(return_value=None)
        mock_dept_repo.get_by_code = AsyncMock(return_value=None)
        mock_dept_repo.get_by_id = AsyncMock(return_value=None)

        dto = DepartmentCreateDTO(name="子部门", code="sub", parentId="non-existent", isActive=1)
        with pytest.raises(BusinessError) as exc_info:
            await dept_service.create_department(dto)
        assert "父部门" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_department_success(self, dept_service, mock_dept_repo):
        """测试更新部门成功。"""
        existing = DepartmentEntity(id="1", name="旧部门", code="old")
        updated = DepartmentEntity(id="1", name="新部门", code="new")
        mock_dept_repo.get_by_id = AsyncMock(side_effect=[existing, updated])
        mock_dept_repo.update = AsyncMock(return_value=updated)

        dto = DepartmentUpdateDTO(name="新部门")
        result = await dept_service.update_department("1", dto)
        assert result.name == "新部门"

    @pytest.mark.asyncio
    async def test_update_department_not_found(self, dept_service, mock_dept_repo):
        """测试更新不存在的部门。"""
        mock_dept_repo.get_by_id = AsyncMock(return_value=None)

        dto = DepartmentUpdateDTO(name="新部门")
        with pytest.raises(NotFoundError):
            await dept_service.update_department("non-existent", dto)

    @pytest.mark.asyncio
    async def test_update_department_circular_reference(self, dept_service, mock_dept_repo):
        """测试更新部门时循环引用。"""
        dept = DepartmentEntity(id="dept-1", name="部门")
        mock_dept_repo.get_by_id = AsyncMock(return_value=dept)

        dto = DepartmentUpdateDTO(parentId="dept-1")
        with pytest.raises(BusinessError) as exc_info:
            await dept_service.update_department("dept-1", dto)
        assert "自己" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_department_success(self, dept_service, mock_dept_repo):
        """测试删除部门成功。"""
        dept = DepartmentEntity(id="1", name="部门")
        mock_dept_repo.get_by_id = AsyncMock(return_value=dept)
        mock_dept_repo.get_by_parent_id = AsyncMock(return_value=[])
        mock_dept_repo.delete = AsyncMock(return_value=True)

        result = await dept_service.delete_department("1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_department_not_found(self, dept_service, mock_dept_repo):
        """测试删除不存在的部门。"""
        mock_dept_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await dept_service.delete_department("non-existent")

    @pytest.mark.asyncio
    async def test_delete_department_with_children(self, dept_service, mock_dept_repo):
        """测试删除有子部门的部门。"""
        dept = DepartmentEntity(id="1", name="父部门")
        child = DepartmentEntity(id="2", name="子部门", parent_id="1")
        mock_dept_repo.get_by_id = AsyncMock(return_value=dept)
        mock_dept_repo.get_by_parent_id = AsyncMock(return_value=[child])

        with pytest.raises(BusinessError) as exc_info:
            await dept_service.delete_department("1")
        assert "子部门" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_dept_tree_empty(self, dept_service, mock_dept_repo):
        """测试获取空部门树。"""
        mock_dept_repo.get_all = AsyncMock(return_value=[])
        tree = await dept_service.get_dept_tree()
        assert tree == []

    @pytest.mark.asyncio
    async def test_get_dept_tree_with_hierarchy(self, dept_service, mock_dept_repo):
        """测试获取多级部门树。"""
        parent = DepartmentEntity(id="1", name="总公司", rank=1)
        child = DepartmentEntity(id="2", name="子公司", parent_id="1", rank=1)
        mock_dept_repo.get_all = AsyncMock(return_value=[parent, child])
        tree = await dept_service.get_dept_tree()
        assert len(tree) == 1
        assert tree[0]["name"] == "总公司"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["name"] == "子公司"

    @pytest.mark.asyncio
    async def test_get_dept_tree_sorted_by_rank(self, dept_service, mock_dept_repo):
        """测试部门树按 rank 排序。"""
        dept2 = DepartmentEntity(id="2", name="B部门", rank=2)
        dept1 = DepartmentEntity(id="1", name="A部门", rank=1)
        mock_dept_repo.get_all = AsyncMock(return_value=[dept2, dept1])
        tree = await dept_service.get_dept_tree()
        assert tree[0]["name"] == "A部门"
        assert tree[1]["name"] == "B部门"

    @pytest.mark.asyncio
    async def test_get_departments_with_active_filter(self, dept_service, mock_dept_repo):
        """测试按启用状态筛选部门。"""
        d = DepartmentEntity(id="1", name="技术部", is_active=0)
        mock_dept_repo.get_filtered = AsyncMock(return_value=[d])
        query = DepartmentListQueryDTO(isActive=0)
        result = await dept_service.get_departments(query)
        assert len(result) == 1
        assert result[0].isActive == 0

    @pytest.mark.asyncio
    async def test_create_department_with_full_fields(self, dept_service, mock_dept_repo):
        """测试创建部门包含所有字段。"""
        mock_dept_repo.get_by_name = AsyncMock(return_value=None)
        mock_dept_repo.get_by_code = AsyncMock(return_value=None)
        created = DepartmentEntity(
            id="1",
            name="技术部",
            code="tech",
            mode_type=1,
            rank=10,
            auto_bind=1,
            is_active=1,
            parent_id=None,
        )
        mock_dept_repo.create = AsyncMock(return_value=created)

        dto = DepartmentCreateDTO(
            name="技术部",
            code="tech",
            modeType=1,
            rank=10,
            autoBind=1,
            isActive=1,
        )
        result = await dept_service.create_department(dto)
        assert result.name == "技术部"
        assert result.code == "tech"
        assert result.modeType == 1
        assert result.rank == 10
        assert result.autoBind == 1

    @pytest.mark.asyncio
    async def test_update_department_parent_not_found(self, dept_service, mock_dept_repo):
        """测试更新部门时设置不存在的父部门。"""
        dept = DepartmentEntity(id="1", name="部门")
        mock_dept_repo.get_by_id = AsyncMock(side_effect=[dept, None])

        dto = DepartmentUpdateDTO(parentId="non-existent")
        with pytest.raises(BusinessError) as exc_info:
            await dept_service.update_department("1", dto)
        assert "父部门" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_department_parent_id_cleared(self, dept_service, mock_dept_repo):
        """测试更新部门时清除 parentId。"""
        dept = DepartmentEntity(id="1", name="部门", parent_id="parent-1")
        updated = DepartmentEntity(id="1", name="部门", parent_id=None)
        mock_dept_repo.get_by_id = AsyncMock(side_effect=[dept, updated])
        mock_dept_repo.update = AsyncMock(return_value=updated)

        dto = DepartmentUpdateDTO(parentId="")
        result = await dept_service.update_department("1", dto)
        assert result.parentId is None

    def test_to_response(self, dept_service):
        """测试 _to_response 静态方法。"""
        from datetime import datetime
        now = datetime.now()
        dept = DepartmentEntity(
            id="1",
            name="技术部",
            code="tech",
            mode_type=1,
            rank=5,
            auto_bind=1,
            is_active=1,
            parent_id="0",
            creator_id="u1",
            modifier_id="u2",
            created_time=now,
            updated_time=now,
            description="描述",
        )
        result = dept_service._to_response(dept)
        assert result.id == "1"
        assert result.name == "技术部"
        assert result.code == "tech"
        assert result.modeType == 1
        assert result.rank == 5
        assert result.autoBind == 1
        assert result.isActive == 1
        assert result.parentId == "0"
        assert result.creatorId == "u1"
        assert result.description == "描述"
