"""UserService._resolve_data_scope 数据权限解析单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.services.user_service import UserService
from src.domain.entities.user import UserEntity
from src.domain.enums import DataScope, UserRole


@pytest.mark.unit
class TestResolveDataScope:
    """数据权限范围解析逻辑测试。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_dept_repo(self):
        return AsyncMock()

    @pytest.fixture
    def user_service(self, mock_user_repo, mock_role_repo, mock_dept_repo):
        """创建带部门仓储的用户服务实例。"""
        return UserService(
            repo=mock_user_repo, password_service=AsyncMock(), role_repo=mock_role_repo, dept_repo=mock_dept_repo
        )

    @staticmethod
    def _make_operator(dept_id: str | None = "dept-1", superuser: bool = False) -> UserEntity:
        """构造测试用操作人实体。"""
        return UserEntity(
            id="op-1",
            username="operator",
            password="",
            is_superuser=UserRole.SUPERUSER if superuser else UserRole.USER,
            dept_id=dept_id,
        )

    async def test_no_operator_returns_unrestricted(self, user_service, mock_user_repo):
        """未传操作人 ID 时不做数据权限过滤。"""
        result = await user_service._resolve_data_scope(None)
        assert result == (None, None)
        mock_user_repo.get_by_id.assert_not_called()

    async def test_operator_not_found_returns_unrestricted(self, user_service, mock_user_repo):
        """操作人不存在时不过滤（交由上层鉴权处理）。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)
        assert await user_service._resolve_data_scope("op-x") == (None, None)

    async def test_superuser_returns_unrestricted(self, user_service, mock_user_repo, mock_role_repo):
        """超级管理员不受数据权限限制。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator(superuser=True))
        assert await user_service._resolve_data_scope("op-1") == (None, None)
        mock_role_repo.get_user_data_scope.assert_not_called()

    async def test_scope_all_returns_unrestricted(self, user_service, mock_user_repo, mock_role_repo):
        """全部数据权限不过滤。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator())
        mock_role_repo.get_user_data_scope = AsyncMock(return_value=int(DataScope.ALL))
        assert await user_service._resolve_data_scope("op-1") == (None, None)

    async def test_scope_self_limits_to_operator(self, user_service, mock_user_repo, mock_role_repo):
        """仅本人数据权限返回操作人 ID 限定。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator())
        mock_role_repo.get_user_data_scope = AsyncMock(return_value=int(DataScope.SELF))
        assert await user_service._resolve_data_scope("op-1") == (None, "op-1")

    async def test_scope_dept_limits_to_own_dept(self, user_service, mock_user_repo, mock_role_repo):
        """本部门数据权限返回操作人所属部门。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator(dept_id="dept-1"))
        mock_role_repo.get_user_data_scope = AsyncMock(return_value=int(DataScope.DEPT))
        assert await user_service._resolve_data_scope("op-1") == (["dept-1"], None)

    async def test_scope_dept_without_dept_returns_empty(self, user_service, mock_user_repo, mock_role_repo):
        """本部门数据权限但操作人无部门时无可见数据。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator(dept_id=None))
        mock_role_repo.get_user_data_scope = AsyncMock(return_value=int(DataScope.DEPT))
        assert await user_service._resolve_data_scope("op-1") == ([], None)

    async def test_scope_dept_and_child_includes_children(
        self, user_service, mock_user_repo, mock_role_repo, mock_dept_repo
    ):
        """本部门及以下数据权限包含子部门。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator(dept_id="dept-1"))
        mock_role_repo.get_user_data_scope = AsyncMock(return_value=int(DataScope.DEPT_AND_CHILD))
        mock_dept_repo.get_child_dept_ids = AsyncMock(return_value=["dept-1-1", "dept-1-2"])
        assert await user_service._resolve_data_scope("op-1") == (["dept-1", "dept-1-1", "dept-1-2"], None)

    async def test_scope_dept_and_child_without_dept_repo(self, mock_user_repo, mock_role_repo):
        """未注入部门仓储时本部门及以下退化为仅本部门。"""
        service = UserService(
            repo=mock_user_repo, password_service=AsyncMock(), role_repo=mock_role_repo, dept_repo=None
        )
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator(dept_id="dept-1"))
        mock_role_repo.get_user_data_scope = AsyncMock(return_value=int(DataScope.DEPT_AND_CHILD))
        assert await service._resolve_data_scope("op-1") == (["dept-1"], None)

    async def test_scope_dept_and_child_without_dept_returns_empty(self, user_service, mock_user_repo, mock_role_repo):
        """本部门及以下数据权限但操作人无部门时无可见数据。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator(dept_id=None))
        mock_role_repo.get_user_data_scope = AsyncMock(return_value=int(DataScope.DEPT_AND_CHILD))
        assert await user_service._resolve_data_scope("op-1") == ([], None)

    async def test_scope_custom_uses_role_linked_depts(self, user_service, mock_user_repo, mock_role_repo):
        """自定义数据权限返回角色关联的部门并集。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=self._make_operator())
        mock_role_repo.get_user_data_scope = AsyncMock(return_value=int(DataScope.CUSTOM))
        mock_role_repo.get_user_custom_dept_ids = AsyncMock(return_value=["dept-9", "dept-8"])
        assert await user_service._resolve_data_scope("op-1") == (["dept-9", "dept-8"], None)
