"""用户服务的单元测试。"""

from unittest.mock import AsyncMock, patch

import pytest

from src.application.dto.user_dto import UserCreateDTO
from src.application.services.user_service import UserService
from src.core.exceptions import ConflictError, NotFoundError
from src.domain.services.password_service import PasswordService
from src.infrastructure.database.models import User


@pytest.mark.unit
class TestUserService:
    """UserService 测试类。"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话。"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def mock_user_repo(self):
        """创建模拟用户仓储。"""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def mock_role_repo(self):
        """创建模拟角色仓储。"""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def mock_password_service(self):
        """创建模拟密码服务。"""
        service = AsyncMock()
        service.hash_password = PasswordService.hash_password
        service.verify_password = PasswordService.verify_password
        return service

    @pytest.fixture
    def user_service(self, mock_session, mock_user_repo, mock_password_service, mock_role_repo):
        """创建用户服务实例（使用依赖注入模式）。"""
        return UserService(session=mock_session, repo=mock_user_repo, password_service=mock_password_service, role_repo=mock_role_repo)

    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_user_repo):
        """测试创建用户成功。"""
        # 设置模拟返回值
        mock_user_repo.get_by_username = AsyncMock(return_value=None)
        mock_user_repo.get_by_email = AsyncMock(return_value=None)

        # 创建测试用户
        test_user = User(id="test-id", username="testuser", email="test@example.com", hashed_password="hashed", nickname="测试用户", status=1)
        mock_user_repo.create = AsyncMock(return_value=test_user)

        # 使用 patch 替换仓储
        with patch.object(user_service, "repo", mock_user_repo):
            dto = UserCreateDTO(username="testuser", password="TestPass123", nickname="测试用户", email="test@example.com", status=1)
            result = await user_service.create_user(dto)

        assert result.username == "testuser"
        assert result.nickname == "测试用户"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_service, mock_user_repo):
        """测试创建用户时用户名重复。"""
        existing_user = User(username="existinguser")
        mock_user_repo.get_by_username = AsyncMock(return_value=existing_user)

        with patch.object(user_service, "repo", mock_user_repo):
            dto = UserCreateDTO(username="existinguser", password="TestPass123", status=1)
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
    async def test_update_status_success(self, user_service, mock_user_repo):
        """测试更新用户状态成功。"""
        mock_user_repo.update_status = AsyncMock(return_value=True)

        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.update_status("test-id", 0)
            assert result is True

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, user_service, mock_user_repo):
        """测试更新不存在用户的状态。"""
        mock_user_repo.update_status = AsyncMock(return_value=False)

        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(NotFoundError):
            await user_service.update_status("non-existent-id", 0)

    @pytest.mark.asyncio
    async def test_reset_password_success(self, user_service, mock_user_repo):
        """测试重置密码成功。"""
        test_user = User(id="test-id", username="testuser")
        mock_user_repo.get_by_id = AsyncMock(return_value=test_user)
        mock_user_repo.reset_password = AsyncMock(return_value=True)

        with patch.object(user_service, "repo", mock_user_repo):
            result = await user_service.reset_password("test-id", "NewPass123")
            assert result is True

    @pytest.mark.asyncio
    async def test_reset_password_not_found(self, user_service, mock_user_repo):
        """测试重置不存在用户的密码。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)

        with patch.object(user_service, "repo", mock_user_repo), pytest.raises(NotFoundError):
            await user_service.reset_password("non-existent-id", "NewPass123")
