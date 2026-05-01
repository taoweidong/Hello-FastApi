"""SystemConfigRepository 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.system_config import SystemConfigEntity
from src.infrastructure.repositories.system_config_repository import SystemConfigRepository


@pytest.mark.unit
class TestSystemConfigRepository:
    """SystemConfigRepository 测试类。"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return SystemConfigRepository(mock_session)

    def test_init(self, repo, mock_session):
        """测试初始化设置 session 和 crud。"""
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        """测试 get_all 返回配置列表。"""
        mock_result = MagicMock()
        mock_model = MagicMock()
        mock_model.to_domain.return_value = SystemConfigEntity(id="1", key="site_name", value="MyApp")
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(page_num=1, page_size=10)
        assert len(result) == 1
        assert result[0].key == "site_name"

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, repo, mock_session):
        """测试 get_all 带筛选条件。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(key="site", is_active=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_count(self, repo, mock_session):
        """测试 count 返回总数。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 10
        mock_session.exec.return_value = mock_result

        result = await repo.count()
        assert result == 10

    @pytest.mark.asyncio
    async def test_count_with_filters(self, repo, mock_session):
        """测试 count 支持筛选。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 3
        mock_session.exec.return_value = mock_result

        result = await repo.count(key="site", is_active=1)
        assert result == 3

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo):
        """测试 get_by_id 找到配置。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = SystemConfigEntity(id="1", key="site_name", value="MyApp")
        repo._crud.get = AsyncMock(return_value=mock_model)

        result = await repo.get_by_id("1")
        assert result is not None
        assert result.key == "site_name"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo):
        """测试 get_by_id 未找到返回 None。"""
        repo._crud.get = AsyncMock(return_value=None)
        result = await repo.get_by_id("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_key_found(self, repo):
        """测试 get_by_key 找到配置。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = SystemConfigEntity(id="1", key="site_name", value="MyApp")
        repo._crud.get = AsyncMock(return_value=mock_model)

        result = await repo.get_by_key("site_name")
        assert result is not None
        assert result.value == "MyApp"

    @pytest.mark.asyncio
    async def test_get_by_key_not_found(self, repo):
        """测试 get_by_key 未找到返回 None。"""
        repo._crud.get = AsyncMock(return_value=None)
        result = await repo.get_by_key("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_session):
        """测试 create 创建配置。"""
        entity = SystemConfigEntity(id="1", key="new_key", value="new_value")
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity
        repo.get_by_id = AsyncMock(return_value=entity)

        with patch(
            "src.infrastructure.repositories.system_config_repository.SystemConfig.from_domain", return_value=mock_model
        ):
            result = await repo.create(entity)

        assert result is not None
        assert result.key == "new_key"
        mock_session.add.assert_called_once_with(mock_model)

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_session):
        """测试 update 更新配置。"""
        entity = SystemConfigEntity(
            id="1",
            key="site_name",
            value="Updated",
            is_active=1,
            access="public",
            inherit=0,
            creator_id="u1",
            modifier_id="u2",
            description="desc",
        )
        repo.get_by_id = AsyncMock(return_value=entity)

        result = await repo.update(entity)

        assert result is not None
        assert result.value == "Updated"

    @pytest.mark.asyncio
    async def test_delete_success(self, repo, mock_session):
        """测试 delete 成功删除。"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.exec.return_value = mock_result

        result = await repo.delete("config-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repo, mock_session):
        """测试 delete 未找到返回 False。"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.exec.return_value = mock_result

        result = await repo.delete("not-exist")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_no_filters(self, repo, mock_session):
        """测试 get_all 无筛选条件。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_key_only(self, repo, mock_session):
        """测试 get_all 仅按 key 筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(key="site")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_all_is_active_only(self, repo, mock_session):
        """测试 get_all 仅按启用状态筛选。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(is_active=1)

        assert result == []
