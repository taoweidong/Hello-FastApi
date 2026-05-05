"""DictionaryRepository 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.entities.dictionary import DictionaryEntity
from src.infrastructure.repositories.dictionary_repository import DictionaryRepository


@pytest.mark.unit
class TestDictionaryRepository:
    """DictionaryRepository 测试类。"""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return DictionaryRepository(mock_session)

    def test_init(self, repo, mock_session):
        """测试初始化设置 session。"""
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        """测试 get_all 返回排序后的字典列表。"""
        mock_d1 = MagicMock()
        mock_d1.to_domain.return_value = DictionaryEntity(id="1", name="gender", label="男", value="1", sort=2)
        mock_d2 = MagicMock()
        mock_d2.to_domain.return_value = DictionaryEntity(id="2", name="gender", label="女", value="0", sort=1)
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_d1, mock_d2]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, mock_session):
        """测试 get_by_id 找到字典。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DictionaryEntity(id="1", name="gender", label="男")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("1")
        assert result is not None

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
        """测试 get_by_name 找到字典。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DictionaryEntity(id="1", name="gender", label="男")
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_name("gender")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_parent_id(self, repo, mock_session):
        """测试 get_by_parent_id 返回子字典。"""
        mock_child = MagicMock()
        mock_child.to_domain.return_value = DictionaryEntity(id="2", name="gender", label="男", sort=1, parent_id="1")
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_child]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_parent_id("1")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_max_sort(self, repo, mock_session):
        """测试 get_max_sort 返回最大排序值。"""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        mock_session.exec.return_value = mock_result

        result = await repo.get_max_sort("parent-1")

        assert result == 10

    @pytest.mark.asyncio
    async def test_get_max_sort_default(self, repo, mock_session):
        """测试 get_max_sort 无数据时返回 0。"""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.exec.return_value = mock_result

        result = await repo.get_max_sort(None)

        assert result == 0

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_session):
        """测试 create 创建字典。"""
        entity = DictionaryEntity(id="1", name="gender", label="男", value="1")
        mock_model = MagicMock()
        mock_model.id = "1"
        mock_model.to_domain.return_value = entity

        def exec_side_effect(stmt):
            mock_result = MagicMock()
            mock_result.first.return_value = mock_model
            return mock_result

        mock_session.exec = AsyncMock(side_effect=exec_side_effect)

        with patch(
            "src.infrastructure.repositories.dictionary_repository.Dictionary.from_domain", return_value=mock_model
        ):
            result = await repo.create(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_session):
        """测试 update 更新字典。"""
        entity = DictionaryEntity(
            id="1", name="gender", label="女", value="0", sort=2, is_active=1, parent_id=None, description="desc"
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

        result = await repo.delete("dict-1")

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
    async def test_get_filtered(self, repo, mock_session):
        """测试 get_filtered 返回过滤列表。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DictionaryEntity(id="1", name="gender", label="男", sort=1)
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_filtered(name="gender", is_active=1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_filtered_no_filters(self, repo, mock_session):
        """测试 get_filtered 无筛选条件。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
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
    async def test_get_all_empty(self, repo, mock_session):
        """测试 get_all 无数据返回空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_parent_id_none(self, repo, mock_session):
        """测试 get_by_parent_id(None) 返回根字典。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_parent_id(None)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_filtered_name_only(self, repo, mock_session):
        """测试 get_filtered 仅按名称筛选。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DictionaryEntity(id="1", name="gender", label="男", sort=1)
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_filtered(name="gender")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_filtered_is_active_only(self, repo, mock_session):
        """测试 get_filtered 仅按状态筛选。"""
        mock_model = MagicMock()
        mock_model.to_domain.return_value = DictionaryEntity(id="1", name="gender", label="男", sort=1)
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_filtered(is_active=1)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_max_sort_scalar_none(self, repo, mock_session):
        """测试 get_max_sort 返回 None 时默认 0。"""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.exec.return_value = mock_result

        result = await repo.get_max_sort("parent-1")

        assert result == 0