"""DepartmentRepository 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.department import DepartmentEntity
from src.infrastructure.repositories.department_repository import DepartmentRepository


@pytest.mark.unit
class TestDepartmentRepository:
    """DepartmentRepository 测试类。"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return DepartmentRepository(mock_session)

    def test_init(self, repo, mock_session):
        """测试初始化设置 session。"""
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        """测试 get_all 返回排序后的部门列表。"""
        mock_dept1 = MagicMock()
        mock_dept1.to_domain.return_value = DepartmentEntity(id="1", name="技术部", code="tech", rank=2)
        mock_dept2 = MagicMock()
        mock_dept2.to_domain.return_value = DepartmentEntity(id="2", name="人事部", code="hr", rank=1)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_dept1, mock_dept2]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, mock_session):
        """测试 get_by_id 找到部门。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DepartmentEntity(id="1", name="技术部", code="tech")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("1")
        assert result is not None
        assert result.id == "1"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo, mock_session):
        """测试 get_by_id 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_found(self, repo, mock_session):
        """测试 get_by_name 找到部门。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DepartmentEntity(id="1", name="技术部", code="tech")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_name("技术部")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_code_found(self, repo, mock_session):
        """测试 get_by_code 找到部门。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DepartmentEntity(id="1", name="技术部", code="tech")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_code("tech")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_parent_id(self, repo, mock_session):
        """测试 get_by_parent_id 返回子部门列表。"""
        mock_child = MagicMock()
        mock_child.to_domain.return_value = DepartmentEntity(id="2", name="前端组", code="fe", rank=1, parent_id="1")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_child]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_parent_id("1")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_parent_id_none(self, repo, mock_session):
        """测试 get_by_parent_id(None) 返回根部门。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_parent_id(None)
        assert result == []

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_session):
        """测试 create 创建部门。"""
        entity = DepartmentEntity(id="1", name="新部门", code="new")
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.first.return_value = mock_model
            return mock_result

        mock_session.exec = AsyncMock(side_effect=exec_side_effect)

        with patch(
            "src.infrastructure.repositories.department_repository.Department.from_domain", return_value=mock_model
        ):
            result = await repo.create(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_session):
        """测试 update 更新部门。"""
        entity = DepartmentEntity(
            id="1",
            name="更新后",
            code="upd",
            mode_type=1,
            rank=2,
            auto_bind=1,
            is_active=1,
            creator_id="u1",
            modifier_id="u2",
            parent_id=None,
            description="desc",
        )
        mock_merged = MagicMock()
        mock_merged.id = "1"
        mock_merged.to_domain.return_value = entity

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.first.return_value = mock_merged
            return mock_result

        mock_session.exec = AsyncMock(side_effect=exec_side_effect)

        result = await repo.update(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_success(self, repo, mock_session):
        """测试 delete 成功删除。"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.delete("dept-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repo, mock_session):
        """测试 delete 未找到返回 False。"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.delete("not-exist")

        assert result is False

    @pytest.mark.asyncio
    async def test_count(self, repo, mock_session):
        """测试 count 返回总数。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 5
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count()

        assert result == 5

    @pytest.mark.asyncio
    async def test_count_with_filters(self, repo, mock_session):
        """测试 count 支持筛选。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 3
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count(name="技术", is_active=1)

        assert result == 3

    @pytest.mark.asyncio
    async def test_get_filtered(self, repo, mock_session):
        """测试 get_filtered 返回过滤列表。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DepartmentEntity(id="1", name="技术部", code="tech", rank=1)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_filtered(name="技术", is_active=1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_filtered_no_filters(self, repo, mock_session):
        """测试 get_filtered 无筛选条件。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_filtered()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, repo, mock_session):
        """测试 get_by_name 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_name("not-exist")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_code_not_found(self, repo, mock_session):
        """测试 get_by_code 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_code("not-exist")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_empty(self, repo, mock_session):
        """测试 get_all 无数据返回空列表。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_filtered_name_only(self, repo, mock_session):
        """测试 get_filtered 仅按名称筛选。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DepartmentEntity(id="1", name="技术部", code="tech", rank=1)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_filtered(name="技术")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_filtered_is_active_only(self, repo, mock_session):
        """测试 get_filtered 仅按状态筛选。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DepartmentEntity(id="1", name="技术部", code="tech", rank=1)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_filtered(is_active=1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_by_parent_id_empty(self, repo, mock_session):
        """测试 get_by_parent_id 无子部门返回空列表。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_parent_id("parent-1")

        assert result == []

    @pytest.mark.asyncio
    async def test_count_no_filters(self, repo, mock_session):
        """测试 count 无筛选参数。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 10
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count()

        assert result == 10