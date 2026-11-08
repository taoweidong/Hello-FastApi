"""ExampleDataService（Univer 表格 CRUD 示例）单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.example_data_dto import (
    ExampleDataBatchItem,
    ExampleDataBatchSaveDTO,
    ExampleDataCreateDTO,
    ExampleDataListQueryDTO,
    ExampleDataUpdateDTO,
)
from src.application.services.example_data_service import ExampleDataService
from src.domain.entities.example_data import ExampleDataEntity
from src.domain.exceptions import BusinessError, NotFoundError


def make_row(idx: int = 1, **kw) -> ExampleDataEntity:
    defaults = dict(id=f"ex-{idx}", name=f"row{idx}", quantity=idx, price=1.5)
    defaults.update(kw)
    return ExampleDataEntity(**defaults)


@pytest.mark.unit
class TestExampleDataService:
    @pytest.fixture
    def repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, repo):
        return ExampleDataService(repo=repo, cache_service=None)

    async def test_get_rows_returns_page(self, service, repo):
        repo.count = AsyncMock(return_value=1)
        repo.get_all = AsyncMock(return_value=[make_row(1)])

        rows, total = await service.get_rows(ExampleDataListQueryDTO(pageNum=1, pageSize=10))

        assert total == 1
        assert rows[0].name == "row1"

    async def test_create_row_duplicate_name_raises(self, service, repo):
        repo.get_all = AsyncMock(return_value=[make_row(1, name="dup")])
        with pytest.raises(BusinessError, match="已存在"):
            await service.create_row(ExampleDataCreateDTO(name="dup"))

    async def test_create_row_ok(self, service, repo):
        repo.get_all = AsyncMock(return_value=[])
        repo.create = AsyncMock(side_effect=lambda e: e)

        row = await service.create_row(ExampleDataCreateDTO(name="new", quantity=3, price=2.5))

        assert row.name == "new"
        assert row.quantity == 3

    async def test_update_row_missing_raises(self, service, repo):
        repo.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(NotFoundError):
            await service.update_row("nope", ExampleDataUpdateDTO(name="x"))

    async def test_update_row_full_write(self, service, repo):
        entity = make_row(1)
        repo.get_by_id = AsyncMock(return_value=entity)
        repo.update = AsyncMock(side_effect=lambda e: e)

        row = await service.update_row("ex-1", ExampleDataUpdateDTO(name="updated", quantity=9, isActive=0))

        assert row.name == "updated"
        assert row.quantity == 9
        assert row.isActive == 0

    async def test_delete_row_missing_raises(self, service, repo):
        repo.delete = AsyncMock(return_value=False)
        with pytest.raises(NotFoundError):
            await service.delete_row("nope")

    async def test_batch_save_creates_updates_deletes(self, service, repo):
        repo.get_all = AsyncMock(return_value=[])  # 名称查重通过
        repo.create = AsyncMock(side_effect=lambda e: e)
        repo.get_by_id = AsyncMock(return_value=make_row(1))
        repo.update = AsyncMock(side_effect=lambda e: e)
        repo.batch_delete = AsyncMock(return_value=2)

        dto = ExampleDataBatchSaveDTO(
            creates=[ExampleDataBatchItem(name="c1")],
            updates=[ExampleDataBatchItem(id="ex-1", name="u1")],
            deletes=["ex-9", "ex-8"],
        )
        result = await service.batch_save(dto, operator_id="admin")

        assert result == {"created": 1, "updated": 1, "deleted": 2}
        repo.batch_delete.assert_awaited_once_with(["ex-9", "ex-8"])

    async def test_batch_save_update_without_id_raises(self, service, repo):
        dto = ExampleDataBatchSaveDTO(updates=[ExampleDataBatchItem(name="no-id")])
        with pytest.raises(BusinessError, match="缺少 id"):
            await service.batch_save(dto)

    async def test_batch_save_create_duplicate_raises(self, service, repo):
        repo.get_all = AsyncMock(return_value=[make_row(1, name="dup")])
        dto = ExampleDataBatchSaveDTO(creates=[ExampleDataBatchItem(name="dup")])
        with pytest.raises(BusinessError, match="已存在"):
            await service.batch_save(dto)
