"""UserRepository 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.user import UserEntity
from src.infrastructure.repositories.user_repository import UserRepository


@pytest.mark.unit
class TestUserRepository:
    """UserRepository 测试类。"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return UserRepository(mock_session)

    def test_init(self, repo, mock_session):
        """测试初始化设置 session。"""
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, mock_session):
        """测试 get_by_id 找到用户。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = UserEntity(id="1", username="admin", password="hash")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("1")
        assert result is not None
        assert result.username == "admin"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo, mock_session):
        """测试 get_by_id 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_username_found(self, repo, mock_session):
        """测试 get_by_username 找到用户。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = UserEntity(id="1", username="admin", password="hash")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_username("admin")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_email_found(self, repo, mock_session):
        """测试 get_by_email 找到用户。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = UserEntity(
            id="1", username="admin", password="hash", email="admin@test.com"
        )
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_email("admin@test.com")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        """测试 get_all 返回用户分页列表。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = UserEntity(id="1", username="admin", password="hash")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(page_num=1, page_size=10)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, repo, mock_session):
        """测试 get_all 带筛选条件。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(username="admin", phone="138", email="test@test.com", is_active=1, dept_id="dept-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_count(self, repo, mock_session):
        """测试 count 返回总数。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 100
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count()
        assert result == 100

    @pytest.mark.asyncio
    async def test_count_with_filters(self, repo, mock_session):
        """测试 count 支持筛选。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 5
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count(username="admin", is_active=1)
        assert result == 5

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_session):
        """测试 create 创建用户。"""
        entity = UserEntity(id="1", username="newuser", password="hash")
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.first.return_value = mock_model
            return mock_result

        mock_session.exec = AsyncMock(side_effect=exec_side_effect)

        with patch("src.infrastructure.repositories.user_repository.User.from_domain", return_value=mock_model):
            result = await repo.create(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_session):
        """测试 update 更新用户。"""
        entity = UserEntity(id="1", username="updated", password="newhash")
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

        result = await repo.delete("user-1")
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
    async def test_batch_delete(self, repo, mock_session):
        """测试 batch_delete 批量删除用户。"""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.exec = AsyncMock(return_value=mock_result)

        count = await repo.batch_delete(["1", "2", "3"])
        assert count == 3

    @pytest.mark.asyncio
    async def test_batch_delete_empty(self, repo):
        """测试 batch_delete 空列表返回 0。"""
        count = await repo.batch_delete([])
        assert count == 0

    @pytest.mark.asyncio
    async def test_update_status_success(self, repo, mock_session):
        """测试 update_status 更新状态成功。"""
        mock_user = MagicMock()
        mock_user.is_active = 0
        mock_result = MagicMock()
        mock_result.first.return_value = mock_user
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.update_status("user-1", 1)

        assert result is True

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, repo, mock_session):
        """测试 update_status 用户不存在返回 False。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.update_status("not-exist", 1)

        assert result is False

    @pytest.mark.asyncio
    async def test_reset_password_success(self, repo, mock_session):
        """测试 reset_password 重置密码成功。"""
        mock_user = MagicMock()
        mock_user.password = ""
        mock_result = MagicMock()
        mock_result.first.return_value = mock_user
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.reset_password("user-1", "new-hash")

        assert result is True

    @pytest.mark.asyncio
    async def test_reset_password_not_found(self, repo, mock_session):
        """测试 reset_password 用户不存在返回 False。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.reset_password("not-exist", "hash")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, repo, mock_session):
        """测试 get_by_username 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_username("not-exist")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, repo, mock_session):
        """测试 get_by_email 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_email("not-exist@test.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_no_filters(self, repo, mock_session):
        """测试 get_all 无筛选条件。"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert result == []

    @pytest.mark.asyncio
    async def test_count_with_all_filters(self, repo, mock_session):
        """测试 count 使用所有筛选条件。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 3
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count(
            username="admin", phone="138", email="admin@test.com", is_active=1, dept_id="dept-1"
        )

        assert result == 3
