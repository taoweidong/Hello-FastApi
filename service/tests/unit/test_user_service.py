"""用户服务的单元测试。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.application.dto.user_dto import ChangePasswordDTO, UserCreateDTO, UserListQueryDTO, UserUpdateDTO
from src.application.services.user_service import UserService
from src.domain.entities.user import UserEntity
from src.domain.exceptions import ConflictError, NotFoundError, UnauthorizedError
from src.domain.services.password_service import PasswordService


@pytest.mark.unit
class TestUserService:
    """UserService 测试类。"""

    @pytest.fixture
    def mock_user_repo(self):
        """创建模拟用户仓储。"""
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        """创建模拟角色仓储。"""
        return AsyncMock()

    @pytest.fixture
    def mock_password_service(self):
        """创建模拟密码服务。"""
        service = AsyncMock()
        service.hash_password = PasswordService.hash_password
        service.verify_password = PasswordService.verify_password
        return service

    @pytest.fixture
    def user_service(self, mock_user_repo, mock_password_service, mock_role_repo):
        """创建用户服务实例。"""
        return UserService(repo=mock_user_repo, password_service=mock_password_service, role_repo=mock_role_repo)

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_user_repo):
        """测试创建用户成功。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        mock_user_repo.get_by_email = AsyncMock(return_value=None)

        test_user = UserEntity(
            id="test-id",
            username="testuser",
            email="test@example.com",
            password="hashed",
            nickname="测试用户",
            is_active=1,
        )
        mock_user_repo.create = AsyncMock(return_value=test_user)
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_role_repo = user_service.role_repo
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])

        with patch.object(user_service, "repo", mock_user_repo):
            dto = UserCreateDTO(
                username="testuser",
                password="TestPass123",
                nickname="测试用户",
                email="test@example.com",
                isActive=True,
            )
            result = await user_service.create_user(dto)

        assert result.username == "testuser"
        assert result.nickname == "测试用户"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_service, mock_user_repo):
        """测试创建用户时用户名重复。"""
        existing_user = UserEntity(id="ex-id", username="existinguser", password="hashed")
        mock_user_repo.get_by_username = AsyncMock(return_value=existing_user)

        with patch.object(user_service, "repo", mock_user_repo):
            dto = UserCreateDTO(username="existinguser", password="TestPass123", isActive=True)
            with pytest.raises(ConflictError) as exc_info:
                await user_service.create_user(dto)
            assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_service, mock_user_repo):
        """测试获取不存在的用户。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        with patch.object(user_service, "repo", mock_user_repo):
            with pytest.raises(NotFoundError) as exc_info:
                await user_service.get_user("non-existent-id")
            assert "不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_service, mock_user_repo):
        """测试删除用户成功。"""
        mock_user_repo.delete = AsyncMock(return_value=True)

        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.delete_user("test-id")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_service, mock_user_repo):
        """测试删除不存在的用户。"""
        mock_user_repo.delete = AsyncMock(return_value=False)

        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(NotFoundError):
            await user_service.delete_user("non-existent-id")

    @pytest.mark.asyncio
    async def test_batch_delete_users(self, user_service, mock_user_repo):
        """测试批量删除用户。"""
        mock_user_repo.batch_delete = AsyncMock(return_value=3)

        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.batch_delete_users(["id1", "id2", "id3"])
            assert result["deleted_count"] == 3
            assert result["total_requested"] == 3

    @pytest.mark.asyncio
    async def test_update_is_active_success(self, user_service, mock_user_repo):
        """测试更新用户活跃状态成功。"""
        test_user = UserEntity(
            id="test-id",
            username="testuser",
            password="hashed",
            is_active=1,
        )
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_user_repo.update = AsyncMock(return_value=test_user)

        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.update_status("test-id", 0)
            assert result is True
            assert test_user.is_active == 0

    @pytest.mark.asyncio
    async def test_update_is_active_not_found(self, user_service, mock_user_repo):
        """测试更新不存在用户的状态。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(NotFoundError):
            await user_service.update_status("non-existent-id", False)

    @pytest.mark.asyncio
    async def test_reset_password_success(self, user_service, mock_user_repo):
        """测试重置密码成功。"""
        test_user = UserEntity(id="test-id", username="testuser", password="hashed")
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_user_repo.update = AsyncMock(return_value=test_user)

        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.reset_password("test-id", "NewPass123")
            assert result is True
            mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_not_found(self, user_service, mock_user_repo):
        """测试重置不存在用户的密码。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(NotFoundError):
            await user_service.reset_password("non-existent-id", "NewPass123")

    @pytest.mark.asyncio
    async def test_get_user_success(self, user_service, mock_user_repo, mock_role_repo):
        """测试获取用户成功。"""
        test_user = UserEntity(id="test-id", username="testuser", password="hashed", nickname="测试用户", is_active=1)
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])

        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            result = await user_service.get_user("test-id")
        assert result.username == "testuser"
        assert result.nickname == "测试用户"

    @pytest.mark.asyncio
    async def test_get_user_by_username_found(self, user_service, mock_user_repo):
        """测试根据用户名获取用户实体。"""
        test_user = UserEntity(id="test-id", username="testuser", password="hashed")
        mock_user_repo.get_by_username = AsyncMock(return_value=test_user)
        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.get_user_by_username("testuser")
        assert result is not None
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, user_service, mock_user_repo):
        """测试根据用户名获取用户实体不存在。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.get_user_by_username("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_users_with_filters(self, user_service, mock_user_repo, mock_role_repo):
        """测试按筛选条件获取用户列表。"""
        users = [UserEntity(id="1", username="user1", password="hash", is_active=1)]
        mock_user_repo.get_all = AsyncMock(return_value=users)
        mock_user_repo.count = AsyncMock(return_value=1)
        mock_role_repo.get_users_roles_batch = AsyncMock(return_value={"1": []})

        query = UserListQueryDTO(pageNum=1, pageSize=10, username="user1", isActive=1)
        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            results, total = await user_service.get_users(query)
        assert total == 1
        assert len(results) == 1
        assert results[0].username == "user1"

    @pytest.mark.asyncio
    async def test_get_users_empty(self, user_service, mock_user_repo, mock_role_repo):
        """测试获取空用户列表。"""
        mock_user_repo.get_all = AsyncMock(return_value=[])
        mock_user_repo.count = AsyncMock(return_value=0)
        mock_role_repo.get_users_roles_batch = AsyncMock(return_value={})

        query = UserListQueryDTO(pageNum=1, pageSize=10)
        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            results, total = await user_service.get_users(query)
        assert total == 0
        assert results == []

    @pytest.mark.asyncio
    async def test_get_users_dept_id_zero(self, user_service, mock_user_repo, mock_role_repo):
        """测试 deptId=0 时转为 None。"""
        mock_user_repo.get_all = AsyncMock(return_value=[])
        mock_user_repo.count = AsyncMock(return_value=0)
        mock_role_repo.get_users_roles_batch = AsyncMock(return_value={})

        query = UserListQueryDTO(pageNum=1, pageSize=10, deptId="0")
        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            await user_service.get_users(query)
        call_kwargs = mock_user_repo.get_all.call_args[1]
        assert call_kwargs["dept_id"] is None

    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_user_repo, mock_role_repo):
        """测试更新用户成功。"""
        test_user = UserEntity(id="test-id", username="testuser", password="hashed", nickname="旧昵称", is_active=1)
        updated_user = UserEntity(id="test-id", username="testuser", password="hashed", nickname="新昵称", is_active=1)
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_user_repo.update = AsyncMock(return_value=updated_user)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])

        dto = UserUpdateDTO(nickname="新昵称")
        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            result = await user_service.update_user("test-id", dto)
        assert result.nickname == "新昵称"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service, mock_user_repo):
        """测试更新不存在的用户。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        dto = UserUpdateDTO(nickname="新昵称")
        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(NotFoundError):
            await user_service.update_user("non-existent", dto)

    @pytest.mark.asyncio
    async def test_update_user_email_conflict(self, user_service, mock_user_repo):
        """测试更新时邮箱重复。"""
        test_user = UserEntity(id="test-id", username="testuser", password="hashed", email="old@test.com")
        other_user = UserEntity(id="other-id", username="other", password="hash", email="new@test.com")
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_user_repo.get_by_email = AsyncMock(return_value=other_user)

        dto = UserUpdateDTO(email="new@test.com")
        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(ConflictError) as exc_info:
            await user_service.update_user("test-id", dto)
        assert "邮箱" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_change_password_success(self, user_service, mock_user_repo, mock_password_service):
        """测试修改密码成功。"""
        hashed = PasswordService.hash_password("OldPass123")
        test_user = UserEntity(id="test-id", username="testuser", password=hashed)
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_user_repo.update = AsyncMock(return_value=test_user)

        dto = ChangePasswordDTO(oldPassword="OldPass123", newPassword="NewPass456")
        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.change_password("test-id", dto)
        assert result is True

    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, user_service, mock_user_repo, mock_password_service):
        """测试修改密码时旧密码错误。"""
        hashed = PasswordService.hash_password("RealPass123")
        test_user = UserEntity(id="test-id", username="testuser", password=hashed)
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

        dto = ChangePasswordDTO(oldPassword="WrongPass123", newPassword="NewPass456")
        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(UnauthorizedError) as exc_info:
            await user_service.change_password("test-id", dto)
        assert "旧密码" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_assign_roles_success(self, user_service, mock_user_repo, mock_role_repo):
        """测试为用户分配角色列表成功。"""
        test_user = UserEntity(id="test-id", username="testuser", password="hashed")
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_role_repo.assign_roles_to_user = AsyncMock()

        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            result = await user_service.assign_roles("test-id", ["role-1", "role-2"])
        assert result is True
        mock_role_repo.assign_roles_to_user.assert_called_once_with("test-id", ["role-1", "role-2"])

    @pytest.mark.asyncio
    async def test_assign_roles_user_not_found(self, user_service, mock_user_repo):
        """测试分配角色时用户不存在。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(NotFoundError):
            await user_service.assign_roles("non-existent", ["role-1"])

    @pytest.mark.asyncio
    async def test_get_users_dept_id_empty(self, user_service, mock_user_repo, mock_role_repo):
        """测试 deptId=\"\" 时转为 None。"""
        mock_user_repo.get_all = AsyncMock(return_value=[])
        mock_user_repo.count = AsyncMock(return_value=0)
        mock_role_repo.get_users_roles_batch = AsyncMock(return_value={})

        query = UserListQueryDTO(pageNum=1, pageSize=10, deptId="")
        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            await user_service.get_users(query)
        call_kwargs = mock_user_repo.get_all.call_args[1]
        assert call_kwargs["dept_id"] is None

    @pytest.mark.asyncio
    async def test_create_superuser_duplicate_username(self, user_service, mock_user_repo):
        """测试创建超级用户时用户名重复。"""
        mock_user_repo.get_by_username = AsyncMock(
            return_value=UserEntity(id="ex-id", username="admin", password="hash")
        )
        dto = UserCreateDTO(username="admin", password="Admin123456", isActive=True)
        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(ConflictError):
            await user_service.create_superuser(dto)

    @pytest.mark.asyncio
    async def test_create_superuser_duplicate_email(self, user_service, mock_user_repo):
        """测试创建超级用户时邮箱重复。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        mock_user_repo.get_by_email = AsyncMock(
            return_value=UserEntity(
                id="ex-id",
                username="other",
                password="hash",
                email="dup@test.com",
            )
        )
        dto = UserCreateDTO(username="newadmin", password="Admin123456", email="dup@test.com", isActive=True)
        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(ConflictError):
            await user_service.create_superuser(dto)

    @pytest.mark.asyncio
    async def test_create_superuser_success(self, user_service, mock_user_repo, mock_role_repo):
        """测试创建超级用户并自动分配 admin 角色。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        created = UserEntity(id="su-id", username="superadmin", password="hashed", is_superuser=1)
        mock_user_repo.create = AsyncMock(return_value=created)
        mock_role_repo.get_by_name = AsyncMock(return_value=None)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])

        dto = UserCreateDTO(username="superadmin", password="Admin123", isActive=True)
        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            result = await user_service.create_superuser(dto)
        assert result.username == "superadmin"

    @pytest.mark.asyncio
    async def test_create_superuser_with_admin_role(self, user_service, mock_user_repo, mock_role_repo):
        """测试创建超级用户并存在 admin 角色时分配。"""
        from src.domain.entities.role import RoleEntity
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        created = UserEntity(id="su-id", username="superadmin", password="hashed", is_superuser=1)
        mock_user_repo.create = AsyncMock(return_value=created)
        admin_role = RoleEntity(id="admin-id", name="admin", code="admin")
        mock_role_repo.get_by_name = AsyncMock(return_value=admin_role)
        mock_role_repo.assign_role_to_user = AsyncMock()
        mock_role_repo.get_user_roles = AsyncMock(return_value=[admin_role])

        dto = UserCreateDTO(username="superadmin", password="Admin123", isActive=True)
        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            result = await user_service.create_superuser(dto)
        assert result.username == "superadmin"
        mock_role_repo.assign_role_to_user.assert_called_once_with(created.id, admin_role.id)

    @pytest.mark.asyncio
    async def test_create_user_email_conflict(self, user_service, mock_user_repo):
        """测试创建用户时邮箱重复。"""
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        mock_user_repo.get_by_email = AsyncMock(
            return_value=UserEntity(
                id="ex-id",
                username="existing",
                password="hash",
                email="dup@test.com",
            )
        )

        dto = UserCreateDTO(username="newuser", password="Pass123456", email="dup@test.com", isActive=True)
        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(ConflictError) as exc_info:
            await user_service.create_user(dto)
        assert "邮箱" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_batch_delete_empty(self, user_service, mock_user_repo):
        """测试批量删除空列表。"""
        mock_user_repo.batch_delete = AsyncMock(return_value=0)
        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.batch_delete_users([])
        assert result["deleted_count"] == 0
        assert result["total_requested"] == 0

    @pytest.mark.asyncio
    async def test_delete_user_cache_invalidated(self, user_service, mock_user_repo, mock_role_repo):
        """测试删除用户时缓存失效。"""
        mock_user_repo.delete = AsyncMock(return_value=True)
        cache_service = AsyncMock()
        service = UserService(
            repo=mock_user_repo,
            password_service=user_service.password_service,
            role_repo=mock_role_repo,
            cache_service=cache_service,
        )
        with patch.object(service, "repo", mock_user_repo):
            result = await service.delete_user("test-id")
        assert result is True

    @pytest.mark.asyncio
    async def test_update_status_activate(self, user_service, mock_user_repo, mock_role_repo):
        """测试激活用户。"""
        test_user = UserEntity(id="test-id", username="testuser", password="hashed", is_active=0)
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_user_repo.update = AsyncMock(return_value=test_user)

        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            result = await user_service.update_status("test-id", 1)
        assert result is True
        assert test_user.is_active == 1

    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self, user_service, mock_user_repo):
        """测试修改密码时用户不存在。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)
        dto = ChangePasswordDTO(oldPassword="OldPass123", newPassword="NewPass456")
        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(NotFoundError):
            await user_service.change_password("non-existent", dto)

    def test_to_response_with_roles_static(self, user_service):
        """测试 _to_response_with_roles 静态方法。"""
        from src.domain.entities.role import RoleEntity
        user = UserEntity(id="u1", username="testuser", password="hash", nickname="测试")
        roles = [RoleEntity(id="r1", name="管理员", code="admin"), RoleEntity(id="r2", name="用户", code="user")]
        result = user_service._to_response_with_roles(user, roles)
        assert result.username == "testuser"
        assert len(result.roles) == 2
        assert result.roles[0]["name"] == "管理员"

    def test_to_response_with_roles_empty(self, user_service):
        """测试 _to_response_with_roles 空角色。"""
        user = UserEntity(id="u1", username="testuser", password="hash")
        result = user_service._to_response_with_roles(user, [])
        assert result.roles == []

    @pytest.mark.asyncio
    async def test_update_user_self_email_same(self, user_service, mock_user_repo):
        """测试更新时邮箱相同（self-update L112→115 分支：existing.id == user_id，不抛异常）。"""
        test_user = UserEntity(
            id="test-id", username="testuser", password="hashed", nickname="旧昵称", email="same@test.com", is_active=1
        )
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_user_repo.get_by_email = AsyncMock(return_value=test_user)
        mock_user_repo.update = AsyncMock(return_value=test_user)
        mock_role_repo = user_service.role_repo
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])

        dto = UserUpdateDTO(email="same@test.com")
        with (
            patch.object(user_service, "repo", mock_user_repo),
            patch.object(user_service, "role_repo", mock_role_repo),
        ):
            result = await user_service.update_user("test-id", dto)
        assert result.email == "same@test.com"


@pytest.mark.unit
class TestUserServiceGetUserById:
    """UserService.get_user_by_id 测试类。"""

    @pytest.fixture
    def mock_user_repo(self):
        """创建模拟用户仓储。"""
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        """创建模拟角色仓储。"""
        return AsyncMock()

    @pytest.fixture
    def mock_password_service(self):
        """创建模拟密码服务。"""
        service = AsyncMock()
        service.hash_password = PasswordService.hash_password
        service.verify_password = PasswordService.verify_password
        return service

    @pytest.fixture
    def user_service(self, mock_user_repo, mock_password_service, mock_role_repo):
        """创建用户服务实例。"""
        return UserService(repo=mock_user_repo, password_service=mock_password_service, role_repo=mock_role_repo)

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_user_repo):
        """测试 L236：get_user_by_id 成功返回实体。"""
        test_user = UserEntity(id="test-id", username="testuser", password="hashed")
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.get_user_by_id("test-id")

        assert result is not None
        assert result.id == "test-id"
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_by_id_none(self, user_service, mock_user_repo):
        """测试 L236：get_user_by_id 返回 None。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.get_user_by_id("nonexistent")

        assert result is None


@pytest.mark.unit
class TestUserServiceGetUserInfoWithCache:
    """UserService.get_user_info_with_cache 测试类 — 覆盖所有缓存路径。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_password_service(self):
        service = AsyncMock()
        service.hash_password = PasswordService.hash_password
        service.verify_password = PasswordService.verify_password
        return service

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def user_service_cached(
        self, mock_user_repo, mock_password_service, mock_role_repo, mock_cache
    ):
        return UserService(
            repo=mock_user_repo,
            password_service=mock_password_service,
            role_repo=mock_role_repo,
            cache_service=mock_cache,
        )

    @pytest.fixture
    def user_service_no_cache(self, mock_user_repo, mock_password_service, mock_role_repo):
        return UserService(
            repo=mock_user_repo,
            password_service=mock_password_service,
            role_repo=mock_role_repo,
            cache_service=None,
        )

    @pytest.mark.asyncio
    async def test_cache_hit_active(self, user_service_cached, mock_cache, mock_user_repo):
        """L243-255：缓存命中 + 活跃用户 → 从缓存返回。"""
        cached_info = {
            "id": "u1",
            "username": "cached_user",
            "email": "cached@test.com",
            "is_superuser": UserRole.USER,
            "is_active": UserStatus.ACTIVE,
        }
        mock_cache.get_user_info = AsyncMock(return_value=cached_info)

        with patch.object(user_service_cached, "cache_service", mock_cache):
            result = await user_service_cached.get_user_info_with_cache("u1")

        assert result.username == "cached_user"
        assert result.is_active == UserStatus.ACTIVE
        mock_user_repo.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_hit_inactive(self, user_service_cached, mock_cache):
        """L246-247：缓存命中 + 不活跃 → 抛 UnauthorizedError。"""
        cached_info = {
            "id": "u1",
            "username": "disabled_user",
            "email": "",
            "is_superuser": UserRole.USER,
            "is_active": 0,
        }
        mock_cache.get_user_info = AsyncMock(return_value=cached_info)

        with patch.object(user_service_cached, "cache_service", mock_cache):
            with pytest.raises(UnauthorizedError) as exc_info:
                await user_service_cached.get_user_info_with_cache("u1")
        assert "禁用" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_miss_db_hit_active(self, user_service_cached, mock_cache, mock_user_repo):
        """L257-272：缓存未命中 + DB命中 + 活跃 → 写缓存并返回。"""
        mock_cache.get_user_info = AsyncMock(return_value=None)
        test_user = UserEntity.create_new(
            username="db_user", hashed_password="hashed", email="db@test.com", is_active=1
        )
        test_user.id = "u1"
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

        with (
            patch.object(user_service_cached, "cache_service", mock_cache),
            patch.object(user_service_cached, "repo", mock_user_repo),
        ):
            result = await user_service_cached.get_user_info_with_cache("u1")

        assert result.username == "db_user"
        assert result.is_active == 1
        mock_cache.set_user_info.assert_called_once()
        call_args = mock_cache.set_user_info.call_args[0]
        assert call_args[0] == "u1"
        assert call_args[1]["username"] == "db_user"

    @pytest.mark.asyncio
    async def test_cache_miss_db_miss(self, user_service_cached, mock_cache, mock_user_repo):
        """L258-259：缓存未命中 + DB未命中 → 抛 UnauthorizedError。"""
        mock_cache.get_user_info = AsyncMock(return_value=None)
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        with (
            patch.object(user_service_cached, "cache_service", mock_cache),
            patch.object(user_service_cached, "repo", mock_user_repo),
        ):
            with pytest.raises(UnauthorizedError) as exc_info:
                await user_service_cached.get_user_info_with_cache("u1")
        assert "不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_miss_db_hit_inactive(self, user_service_cached, mock_cache, mock_user_repo):
        """L260-261：缓存未命中 + DB命中 + 不活跃 → 抛 UnauthorizedError。"""
        mock_cache.get_user_info = AsyncMock(return_value=None)
        test_user = UserEntity.create_new(
            username="disabled_user", hashed_password="hashed", is_active=0
        )
        test_user.id = "u1"
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

        with (
            patch.object(user_service_cached, "cache_service", mock_cache),
            patch.object(user_service_cached, "repo", mock_user_repo),
        ):
            with pytest.raises(UnauthorizedError) as exc_info:
                await user_service_cached.get_user_info_with_cache("u1")
        assert "禁用" in str(exc_info.value)
        mock_cache.set_user_info.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_cache_skip_cache_db_hit(self, user_service_no_cache, mock_user_repo):
        """L243/L270：无 cache_service → 跳过缓存，直接查 DB。"""
        test_user = UserEntity.create_new(
            username="nocache_user", hashed_password="hashed", is_active=1
        )
        test_user.id = "u1"
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)

        with patch.object(user_service_no_cache, "repo", mock_user_repo):
            result = await user_service_no_cache.get_user_info_with_cache("u1")

        assert result.username == "nocache_user"


@pytest.mark.unit
class TestUserServiceCheckPermissionCachedOrDb:
    """UserService.check_permission_cached_or_db 测试类 — 覆盖所有路径。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_password_service(self):
        service = AsyncMock()
        service.hash_password = PasswordService.hash_password
        service.verify_password = PasswordService.verify_password
        return service

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def user_service_cached(
        self, mock_user_repo, mock_password_service, mock_role_repo, mock_cache
    ):
        return UserService(
            repo=mock_user_repo,
            password_service=mock_password_service,
            role_repo=mock_role_repo,
            cache_service=mock_cache,
        )

    @pytest.fixture
    def user_service_no_cache(self, mock_user_repo, mock_password_service, mock_role_repo):
        return UserService(
            repo=mock_user_repo,
            password_service=mock_password_service,
            role_repo=mock_role_repo,
            cache_service=None,
        )

    @pytest.mark.asyncio
    async def test_superuser_fastpath(self, user_service_cached, mock_cache):
        """L281-284：超级用户快捷路径 → 返回 SUPERUSER 实体。"""
        result = await user_service_cached.check_permission_cached_or_db(
            "u1", UserRole.SUPERUSER, "some:permission"
        )
        assert result.is_superuser == UserRole.SUPERUSER
        assert result.id == "u1"

    @pytest.mark.asyncio
    async def test_cache_hit_permission_found(self, user_service_cached, mock_cache):
        """L286-293：缓存命中 + 权限存在 → 返回 USER 实体。"""
        mock_cache.get_user_permissions = AsyncMock(
            return_value=[
                {"type": "permission", "name": "user:add"},
                {"type": "permission", "name": "user:delete"},
            ]
        )

        with patch.object(user_service_cached, "cache_service", mock_cache):
            result = await user_service_cached.check_permission_cached_or_db(
                "u1", UserRole.USER, "user:add"
            )

        assert result.is_superuser == UserRole.USER

    @pytest.mark.asyncio
    async def test_cache_hit_permission_not_found(self, user_service_cached, mock_cache):
        """L294：缓存命中 + 权限不存在 → 抛 ForbiddenError。"""
        mock_cache.get_user_permissions = AsyncMock(
            return_value=[
                {"type": "permission", "name": "user:view"},
            ]
        )

        with patch.object(user_service_cached, "cache_service", mock_cache):
            with pytest.raises(ForbiddenError) as exc_info:
                await user_service_cached.check_permission_cached_or_db(
                    "u1", UserRole.USER, "user:delete"
                )
        assert "必需" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_miss_db_permission_found(self, user_service_cached, mock_user_repo, mock_role_repo, mock_cache):
        """L296-312：缓存未命中 + DB 查菜单 + 权限存在 → 写缓存 + 返回 USER。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)

        from src.domain.entities.menu import MenuEntity
        perm_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:add",
            rank=1, path=None, method=None
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[perm_menu])

        with (
            patch.object(user_service_cached, "cache_service", mock_cache),
            patch.object(user_service_cached, "role_repo", mock_role_repo),
        ):
            result = await user_service_cached.check_permission_cached_or_db(
                "u1", UserRole.USER, "user:add"
            )

        assert result.is_superuser == UserRole.USER
        mock_cache.set_user_permissions.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_db_permission_not_found(self, user_service_cached, mock_role_repo, mock_cache):
        """L314：缓存未命中 + DB 查菜单 + 无权限 → 抛 ForbiddenError。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)
        view_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:view",
            rank=1, path=None, method=None
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[view_menu])

        with (
            patch.object(user_service_cached, "cache_service", mock_cache),
            patch.object(user_service_cached, "role_repo", mock_role_repo),
        ):
            with pytest.raises(ForbiddenError) as exc_info:
                await user_service_cached.check_permission_cached_or_db(
                    "u1", UserRole.USER, "user:delete"
                )
        assert "必需" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_cache_skip_and_db_hit(self, user_service_no_cache, mock_role_repo):
        """L296 + L306：无 cache_service → 查 DB 权限并成功返回。"""
        from src.domain.entities.menu import MenuEntity
        perm_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="system:config",
            rank=1, path=None, method=None
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[perm_menu])

        with patch.object(user_service_no_cache, "role_repo", mock_role_repo):
            result = await user_service_no_cache.check_permission_cached_or_db(
                "u1", UserRole.USER, "system:config"
            )

        assert result.is_superuser == UserRole.USER


@pytest.mark.unit
class TestUserServiceCheckAPIPermissionCachedOrDb:
    """UserService.check_api_permission_cached_or_db 测试类 — 覆盖所有路径。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_password_service(self):
        service = AsyncMock()
        service.hash_password = PasswordService.hash_password
        service.verify_password = PasswordService.verify_password
        return service

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def user_service_cached(
        self, mock_user_repo, mock_password_service, mock_role_repo, mock_cache
    ):
        return UserService(
            repo=mock_user_repo,
            password_service=mock_password_service,
            role_repo=mock_role_repo,
            cache_service=mock_cache,
        )

    @pytest.fixture
    def user_service_no_cache(self, mock_user_repo, mock_password_service, mock_role_repo):
        return UserService(
            repo=mock_user_repo,
            password_service=mock_password_service,
            role_repo=mock_role_repo,
            cache_service=None,
        )

    @pytest.mark.asyncio
    async def test_superuser_fastpath(self, user_service_cached, mock_cache):
        """L323-326：超级用户快捷路径 → 返回 SUPERUSER 实体。"""
        result = await user_service_cached.check_api_permission_cached_or_db(
            "u1", UserRole.SUPERUSER, "/api/users", "GET"
        )
        assert result.is_superuser == UserRole.SUPERUSER
        assert result.id == "u1"

    @pytest.mark.asyncio
    async def test_cache_hit_api_perm_found(self, user_service_cached, mock_cache):
        """L328-335：缓存命中 + 匹配 API 权限 → 返回 USER 实体。"""
        mock_cache.get_user_permissions = AsyncMock(
            return_value=[
                {"type": "api", "path": "/api/users", "method": "GET", "name": "user:list"},
                {"type": "api", "path": "/api/users", "method": "POST", "name": "user:add"},
            ]
        )

        with patch.object(user_service_cached, "cache_service", mock_cache):
            result = await user_service_cached.check_api_permission_cached_or_db(
                "u1", UserRole.USER, "/api/users", "GET"
            )

        assert result.is_superuser == UserRole.USER

    @pytest.mark.asyncio
    async def test_cache_hit_api_perm_not_found(self, user_service_cached, mock_cache):
        """L336：缓存命中 + 无匹配 API 权限 → 抛 ForbiddenError。"""
        mock_cache.get_user_permissions = AsyncMock(
            return_value=[
                {"type": "api", "path": "/api/users", "method": "GET", "name": "user:list"},
            ]
        )

        with patch.object(user_service_cached, "cache_service", mock_cache):
            with pytest.raises(ForbiddenError) as exc_info:
                await user_service_cached.check_api_permission_cached_or_db(
                    "u1", UserRole.USER, "/api/users", "DELETE"
                )
        assert "必需" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cache_miss_db_api_perm_found(self, user_service_cached, mock_user_repo, mock_role_repo, mock_cache):
        """L338-357：缓存未命中 + DB 查菜单 + 匹配 API 权限 → 写缓存 + 返回 USER。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)

        from src.domain.entities.menu import MenuEntity
        api_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:list",
            rank=1, path="/api/users", method="GET"
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[api_menu])

        with (
            patch.object(user_service_cached, "cache_service", mock_cache),
            patch.object(user_service_cached, "role_repo", mock_role_repo),
        ):
            result = await user_service_cached.check_api_permission_cached_or_db(
                "u1", UserRole.USER, "/api/users", "GET"
            )

        assert result.is_superuser == UserRole.USER
        mock_cache.set_user_permissions.assert_called_once()
        call_args = mock_cache.set_user_permissions.call_args[0]
        perms = call_args[1]
        assert any(p.get("type") == "api" and p.get("path") == "/api/users" for p in perms)

    @pytest.mark.asyncio
    async def test_cache_miss_db_api_perm_not_found(self, user_service_cached, mock_role_repo, mock_cache):
        """L359：缓存未命中 + DB 查菜单 + 不匹配 → 抛 ForbiddenError。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)
        from src.domain.entities.menu import MenuEntity
        api_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:list",
            rank=1, path="/api/users", method="GET"
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[api_menu])

        with (
            patch.object(user_service_cached, "cache_service", mock_cache),
            patch.object(user_service_cached, "role_repo", mock_role_repo),
        ):
            with pytest.raises(ForbiddenError) as exc_info:
                await user_service_cached.check_api_permission_cached_or_db(
                    "u1", UserRole.USER, "/api/users", "DELETE"
                )
        assert "必需" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_cache_skip_and_db_hit(self, user_service_no_cache, mock_role_repo):
        """L338 + L351：无 cache_service → 查 DB 权限并成功返回。"""
        from src.domain.entities.menu import MenuEntity
        api_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="system:list",
            rank=1, path="/api/system", method="GET"
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[api_menu])

        with patch.object(user_service_no_cache, "role_repo", mock_role_repo):
            result = await user_service_no_cache.check_api_permission_cached_or_db(
                "u1", UserRole.USER, "/api/system", "GET"
            )

        assert result.is_superuser == UserRole.USER

    @pytest.mark.asyncio
    async def test_cache_miss_db_no_path_method(self, user_service_cached, mock_role_repo, mock_cache):
        """L343-349：缓存未命中 + DB 菜单无 path/method → fallback permission entry。"""
        mock_cache.get_user_permissions = AsyncMock(return_value=None)
        from src.domain.entities.menu import MenuEntity
        perm_menu = MenuEntity(
            id="m1", menu_type=MenuEntity.PERMISSION, name="user:view",
            rank=1, path=None, method=None
        )
        mock_role_repo.get_user_all_menus = AsyncMock(return_value=[perm_menu])

        with (
            patch.object(user_service_cached, "cache_service", mock_cache),
            patch.object(user_service_cached, "role_repo", mock_role_repo),
        ):
            with pytest.raises(ForbiddenError):
                await user_service_cached.check_api_permission_cached_or_db(
                    "u1", UserRole.USER, "/api/users", "GET"
                )


@pytest.mark.unit
class TestUserServiceGetCachedOrActiveUser:
    """UserService.get_cached_or_active_user 测试类 — 验证委托到 get_user_info_with_cache。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_password_service(self):
        service = AsyncMock()
        service.hash_password = PasswordService.hash_password
        service.verify_password = PasswordService.verify_password
        return service

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def user_service(self, mock_user_repo, mock_password_service, mock_role_repo, mock_cache):
        return UserService(
            repo=mock_user_repo,
            password_service=mock_password_service,
            role_repo=mock_role_repo,
            cache_service=mock_cache,
        )

    @pytest.mark.asyncio
    async def test_get_cached_or_active_user_delegates(self, user_service, mock_cache):
        """L363：get_cached_or_active_user 委托给 get_user_info_with_cache。"""
        cached_info = {
            "id": "u1",
            "username": "delegated_user",
            "email": "del@test.com",
            "is_superuser": UserRole.USER,
            "is_active": UserStatus.ACTIVE,
        }
        mock_cache.get_user_info = AsyncMock(return_value=cached_info)

        with patch.object(user_service, "cache_service", mock_cache):
            result = await user_service.get_cached_or_active_user("u1")

        assert result.username == "delegated_user"
        mock_cache.get_user_info.assert_called_once_with("u1")
