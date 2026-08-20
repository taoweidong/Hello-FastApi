"""UserService 个人资料相关方法单元测试（update_own_profile / update_avatar）。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.user_dto import UserUpdateDTO
from src.application.services.user_service import UserService
from src.domain.entities.user import UserEntity
from src.domain.exceptions import ConflictError, NotFoundError


def _make_user(**overrides) -> UserEntity:
    """构造测试用用户实体。"""
    base = dict(id="user-1", username="alice", password="hashed", nickname="爱丽丝", is_active=1)
    base.update(overrides)
    return UserEntity(**base)


@pytest.mark.unit
class TestUserProfileService:
    """个人资料服务逻辑测试。"""

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_role_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_user_repo, mock_role_repo):
        return UserService(
            repo=mock_user_repo,
            password_service=AsyncMock(),
            role_repo=mock_role_repo,
        )

    async def test_update_own_profile_applies_profile_fields(self, service, mock_user_repo, mock_role_repo):
        """更新个人资料时应用档案字段并返回响应。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=_make_user())
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        mock_user_repo.update = AsyncMock(side_effect=lambda e: e)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])

        dto = UserUpdateDTO(nickname="新昵称", email="new@example.com", phone="13800000000", description="简介")
        result = await service.update_own_profile("user-1", dto)

        assert result.nickname == "新昵称"
        assert result.email == "new@example.com"
        assert result.phone == "13800000000"
        assert result.description == "简介"

    async def test_update_own_profile_ignores_admin_fields(self, service, mock_user_repo, mock_role_repo):
        """自助更新不允许修改状态等管理字段。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=_make_user(is_active=1))
        mock_user_repo.update = AsyncMock(side_effect=lambda e: e)
        mock_role_repo.get_user_roles = AsyncMock(return_value=[])

        dto = UserUpdateDTO(isActive=0, isStaff=1)
        result = await service.update_own_profile("user-1", dto)

        assert result.isActive == 1
        assert result.isStaff == 0

    async def test_update_own_profile_email_conflict(self, service, mock_user_repo):
        """邮箱与其他用户冲突时抛出 ConflictError。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=_make_user())
        mock_user_repo.get_by_email = AsyncMock(return_value=_make_user(id="user-other"))
        with pytest.raises(ConflictError):
            await service.update_own_profile("user-1", UserUpdateDTO(email="taken@example.com"))

    async def test_update_own_profile_not_found(self, service, mock_user_repo):
        """用户不存在时抛出 NotFoundError。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await service.update_own_profile("missing", UserUpdateDTO(nickname="x"))

    async def test_update_avatar_returns_url(self, service, mock_user_repo):
        """更新头像后返回新头像地址。"""
        user = _make_user()
        mock_user_repo.get_by_id = AsyncMock(return_value=user)
        mock_user_repo.update = AsyncMock(side_effect=lambda e: e)

        result = await service.update_avatar("user-1", "/media/avatars/a.png")

        assert result == "/media/avatars/a.png"
        assert user.avatar == "/media/avatars/a.png"

    async def test_update_avatar_not_found(self, service, mock_user_repo):
        """用户不存在时抛出 NotFoundError。"""
        mock_user_repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await service.update_avatar("missing", "/media/avatars/a.png")
