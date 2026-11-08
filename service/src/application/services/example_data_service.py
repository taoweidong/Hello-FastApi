"""应用层 - 示例数据服务（Univer 表格 CRUD 示例）。"""

from src.application.dto.example_data_dto import (
    ExampleDataBatchSaveDTO,
    ExampleDataCreateDTO,
    ExampleDataListQueryDTO,
    ExampleDataResponseDTO,
    ExampleDataUpdateDTO,
)
from src.domain.entities.example_data import ExampleDataEntity
from src.domain.error_messages import ErrorMessages as EM
from src.domain.exceptions import BusinessError, NotFoundError
from src.domain.repositories.example_data_repository import ExampleDataRepositoryInterface
from src.domain.services.cache_port import CachePort


class ExampleDataService:
    """示例数据的用例层（单表 CRUD + Univer 批量回写）。"""

    def __init__(self, repo: ExampleDataRepositoryInterface, cache_service: CachePort | None = None):
        self.repo = repo
        self.cache_service = cache_service

    @staticmethod
    def _to_response(entity: ExampleDataEntity) -> ExampleDataResponseDTO:
        """实体 → 响应 DTO（转换唯一落点）。"""
        return ExampleDataResponseDTO(
            id=entity.id,
            name=entity.name,
            category=entity.category,
            quantity=entity.quantity,
            price=entity.price,
            recordDate=entity.record_date,
            note=entity.note,
            isActive=entity.is_active,
            creatorId=entity.creator_id,
            createdTime=entity.created_time,
            updatedTime=entity.updated_time,
        )

    async def get_rows(self, query: ExampleDataListQueryDTO) -> tuple[list[ExampleDataResponseDTO], int]:
        """分页列表（Univer 页面以大 pageSize 拉全量）。"""
        total = await self.repo.count(name=query.name, category=query.category, is_active=query.isActive)
        rows = await self.repo.get_all(
            page_num=query.pageNum,
            page_size=query.pageSize,
            name=query.name,
            category=query.category,
            is_active=query.isActive,
        )
        return [self._to_response(r) for r in rows], total

    async def get_row(self, row_id: str) -> ExampleDataResponseDTO:
        """按 ID 获取。"""
        entity = await self.repo.get_by_id(row_id)
        if entity is None:
            raise NotFoundError(EM.example_data_not_found_by_id(row_id))
        return self._to_response(entity)

    async def create_row(self, dto: ExampleDataCreateDTO, operator_id: str | None = None) -> ExampleDataResponseDTO:
        """创建单行（名称唯一）。"""
        existing = await self.repo.get_all(page_num=1, page_size=1, name=dto.name)
        if existing:
            raise BusinessError(EM.example_data_name_exists(dto.name))
        entity = ExampleDataEntity(
            name=dto.name,
            category=dto.category,
            quantity=dto.quantity,
            price=dto.price,
            record_date=dto.recordDate,
            note=dto.note,
            creator_id=operator_id,
        )
        created = await self.repo.create(entity)
        return self._to_response(created)

    async def update_row(
        self, row_id: str, dto: ExampleDataUpdateDTO, operator_id: str | None = None
    ) -> ExampleDataResponseDTO:
        """更新单行（全行回写）。"""
        entity = await self.repo.get_by_id(row_id)
        if entity is None:
            raise NotFoundError(EM.example_data_not_found_by_id(row_id))
        entity.update_info(
            name=dto.name,
            category=dto.category,
            quantity=dto.quantity,
            price=dto.price,
            record_date=dto.recordDate,
            note=dto.note,
            is_active=dto.isActive,
        )
        entity.modifier_id = operator_id
        updated = await self.repo.update(entity)
        return self._to_response(updated)

    async def delete_row(self, row_id: str) -> bool:
        """删除单行。"""
        if not await self.repo.delete(row_id):
            raise NotFoundError(EM.example_data_not_found_by_id(row_id))
        return True

    async def batch_delete_rows(self, row_ids: list[str]) -> int:
        """批量删除。"""
        return await self.repo.batch_delete(row_ids)

    async def batch_save(self, dto: ExampleDataBatchSaveDTO, operator_id: str | None = None) -> dict:
        """Univer 差异回写：creates + updates + deletes 单事务执行。

        Returns:
            {"created": n, "updated": n, "deleted": n}
        """
        created = updated = deleted = 0

        for item in dto.creates:
            existing = await self.repo.get_all(page_num=1, page_size=1, name=item.name)
            if existing:
                raise BusinessError(EM.example_data_name_exists(item.name))
            entity = ExampleDataEntity(
                name=item.name,
                category=item.category,
                quantity=item.quantity,
                price=item.price,
                record_date=item.recordDate,
                note=item.note,
                is_active=item.isActive,
                creator_id=operator_id,
            )
            await self.repo.create(entity)
            created += 1

        for item in dto.updates:
            if not item.id:
                raise BusinessError("更新条目缺少 id")
            entity = await self.repo.get_by_id(item.id)
            if entity is None:
                raise NotFoundError(EM.example_data_not_found_by_id(item.id))
            entity.update_info(
                name=item.name,
                category=item.category,
                quantity=item.quantity,
                price=item.price,
                record_date=item.recordDate,
                note=item.note,
                is_active=item.isActive,
            )
            entity.modifier_id = operator_id
            await self.repo.update(entity)
            updated += 1

        if dto.deletes:
            deleted = await self.repo.batch_delete(dto.deletes)

        return {"created": created, "updated": updated, "deleted": deleted}
