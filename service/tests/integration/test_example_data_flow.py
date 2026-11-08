"""示例数据（Univer 表格 CRUD 示例）集成流程测试。"""

import pytest

from src.application.dto.example_data_dto import ExampleDataBatchItem, ExampleDataBatchSaveDTO, ExampleDataListQueryDTO
from src.application.services.example_data_service import ExampleDataService
from src.infrastructure.repositories.example_data_repository import ExampleDataRepository


@pytest.mark.integration
class TestExampleDataFlow:
    async def test_batch_save_and_query_roundtrip(self, db_session):
        repo = ExampleDataRepository(db_session)
        service = ExampleDataService(repo=repo)

        dto = ExampleDataBatchSaveDTO(
            creates=[
                ExampleDataBatchItem(name="季度A", category="销售", quantity=10, price=99.5, note="v1"),
                ExampleDataBatchItem(name="季度B", category="销售", quantity=5, price=49.0),
            ]
        )
        result = await service.batch_save(dto, operator_id="admin")
        assert result == {"created": 2, "updated": 0, "deleted": 0}

        rows, total = await service.get_rows(ExampleDataListQueryDTO(pageNum=1, pageSize=10, category="销售"))
        assert total == 2
        assert {r.name for r in rows} == {"季度A", "季度B"}

        # 更新 + 删除混合回写
        target = next(r for r in rows if r.name == "季度A")
        dto2 = ExampleDataBatchSaveDTO(
            updates=[ExampleDataBatchItem(id=target.id, name="季度A改", quantity=11, price=99.5)],
            deletes=[r.id for r in rows if r.name == "季度B"],
        )
        result2 = await service.batch_save(dto2)
        assert result2 == {"created": 0, "updated": 1, "deleted": 1}

        rows2, total2 = await service.get_rows(ExampleDataListQueryDTO(pageNum=1, pageSize=10))
        assert total2 == 1
        assert rows2[0].name == "季度A改"
        assert rows2[0].quantity == 11

    async def test_batch_save_duplicate_name_400(self, db_session):
        repo = ExampleDataRepository(db_session)
        service = ExampleDataService(repo=repo)
        await service.batch_save(ExampleDataBatchSaveDTO(creates=[ExampleDataBatchItem(name="dup行")]))

        from src.domain.exceptions import BusinessError

        with pytest.raises(BusinessError, match="已存在"):
            await service.batch_save(ExampleDataBatchSaveDTO(creates=[ExampleDataBatchItem(name="dup行")]))
        await db_session.rollback()
