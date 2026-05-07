"""GenericRepository 基类单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel import Field, SQLModel

from src.infrastructure.repositories.base import GenericRepository


class TestModel(SQLModel, table=True):
    __tablename__ = "test_models"
    id: str = Field(primary_key=True)
    name: str


class TestEntity:
    def __init__(self, entity_id: str, name: str) -> None:
        self.id = entity_id
        self.name = name


class ConcreteRepo(GenericRepository[TestModel, TestEntity]):
    @property
    def _model_class(self) -> type[TestModel]:
        return TestModel

    def _to_domain(self, model: TestModel) -> TestEntity:
        return TestEntity(id=model.id, name=model.name)

    def _from_domain(self, entity: TestEntity) -> TestModel:
        return TestModel(id=entity.id, name=entity.name)


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def repo(mock_session):
    return ConcreteRepo(mock_session)


@pytest.mark.unit
class TestGenericRepository:
    def test_init(self, repo, mock_session):
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, mock_session):
        mock_model = MagicMock(spec=TestModel)
        mock_model.id = "1"
        mock_model.name = "test"
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("1")
        assert result is not None
        assert result.id == "1"
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        mock_model = MagicMock(spec=TestModel)
        mock_model.id = "1"
        mock_model.name = "test"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(page_num=1, page_size=10)
        assert len(result) == 1
        assert result[0].id == "1"

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(page_num=1, page_size=10, name="test")
        assert result == []

    @pytest.mark.asyncio
    async def test_count(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.one.return_value = 42
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count()
        assert result == 42

    @pytest.mark.asyncio
    async def test_count_with_filters(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.one.return_value = 5
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count(name="test")
        assert result == 5

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_session):
        entity = TestEntity(id="1", name="new")
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        result = await repo.create(entity)
        assert result.id == "1"
        assert result.name == "new"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_session):
        entity = TestEntity(id="1", name="updated")
        mock_merged = MagicMock(spec=TestModel)
        mock_merged.id = "1"
        mock_merged.name = "updated"
        mock_session.merge = AsyncMock(return_value=mock_merged)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        result = await repo.update(entity)
        assert result.id == "1"
        assert result.name == "updated"

    @pytest.mark.asyncio
    async def test_delete_success(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        result = await repo.delete("1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        result = await repo.delete("not-exist")
        assert result is False

    # ========== 新增方法测试 ==========

    @pytest.mark.asyncio
    async def test_get_one_by_found(self, repo, mock_session):
        """测试 get_one_by 找到实体。"""
        mock_model = MagicMock(spec=TestModel)
        mock_model.id = "1"
        mock_model.name = "test"
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_one_by("name", "test")
        assert result is not None
        assert result.id == "1"
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_one_by_not_found(self, repo, mock_session):
        """测试 get_one_by 未找到返回 None。"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_one_by("name", "not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_one_by_invalid_field(self, repo, mock_session):
        """测试 get_one_by 无效字段返回 None。"""
        result = await repo.get_one_by("invalid_field", "value")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists_true(self, repo, mock_session):
        """测试 exists 存在返回 True。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 1
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.exists("name", "test")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, repo, mock_session):
        """测试 exists 不存在返回 False。"""
        mock_result = MagicMock()
        mock_result.one.return_value = 0
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.exists("name", "not-exist")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_invalid_field(self, repo, mock_session):
        """测试 exists 无效字段返回 False。"""
        result = await repo.exists("invalid_field", "value")
        assert result is False

    @pytest.mark.asyncio
    async def test_batch_delete_success(self, repo, mock_session):
        """测试 batch_delete 批量删除成功。"""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_session.exec = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        result = await repo.batch_delete(["1", "2", "3"])
        assert result == 3

    @pytest.mark.asyncio
    async def test_batch_delete_empty(self, repo, mock_session):
        """测试 batch_delete 空列表返回 0。"""
        result = await repo.batch_delete([])
        assert result == 0
