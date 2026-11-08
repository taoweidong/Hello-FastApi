"""示例数据路由模块（Univer 表格 CRUD 示例）。

单表数据的增删改查；批量保存端点服务于 Univer 电子表格页面的差异回写。
路由前缀: /api/system/example-data
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends

from src.api.common import list_response, success_response
from src.api.common.response_schemas import ApiResponse, PaginatedResponse
from src.api.dependencies import get_current_user_id, require_permission
from src.api.dependencies.example_data_service import get_example_data_service
from src.application.dto.example_data_dto import (
    ExampleDataBatchSaveDTO,
    ExampleDataCreateDTO,
    ExampleDataListQueryDTO,
    ExampleDataResponseDTO,
    ExampleDataUpdateDTO,
)
from src.application.services.example_data_service import ExampleDataService


class ExampleDataRouter(Routable):
    """示例数据路由类（Univer 表格 CRUD 示例）。"""

    @post("", response_model=PaginatedResponse[dict])
    async def get_rows(
        self,
        query: ExampleDataListQueryDTO,
        service: ExampleDataService = Depends(get_example_data_service),
        _: dict = Depends(require_permission("example:view")),
    ) -> dict:
        """分页列表（名称/类别过滤）。"""
        rows, total = await service.get_rows(query)
        return list_response(
            list_data=[r.model_dump() for r in rows], total=total, page_size=query.pageSize, current_page=query.pageNum
        )

    @get("/{row_id}", response_model=ApiResponse[ExampleDataResponseDTO])
    async def get_row(
        self,
        row_id: str,
        service: ExampleDataService = Depends(get_example_data_service),
        _: dict = Depends(require_permission("example:view")),
    ) -> dict:
        """按 ID 获取详情。"""
        row = await service.get_row(row_id)
        return success_response(data=row.model_dump())

    @post("/create", response_model=ApiResponse[ExampleDataResponseDTO])
    async def create_row(
        self,
        dto: ExampleDataCreateDTO,
        service: ExampleDataService = Depends(get_example_data_service),
        user_id: str = Depends(get_current_user_id),
        _: dict = Depends(require_permission("example:add")),
    ) -> dict:
        """创建单行。"""
        row = await service.create_row(dto, operator_id=user_id)
        return success_response(data=row.model_dump(), message="创建成功")

    @put("/{row_id}", response_model=ApiResponse[ExampleDataResponseDTO])
    async def update_row(
        self,
        row_id: str,
        dto: ExampleDataUpdateDTO,
        service: ExampleDataService = Depends(get_example_data_service),
        user_id: str = Depends(get_current_user_id),
        _: dict = Depends(require_permission("example:edit")),
    ) -> dict:
        """更新单行（全行回写）。"""
        row = await service.update_row(row_id, dto, operator_id=user_id)
        return success_response(data=row.model_dump(), message="更新成功")

    @delete("/{row_id}", response_model=ApiResponse[None])
    async def delete_row(
        self,
        row_id: str,
        service: ExampleDataService = Depends(get_example_data_service),
        _: dict = Depends(require_permission("example:delete")),
    ) -> dict:
        """删除单行。"""
        await service.delete_row(row_id)
        return success_response(message="删除成功")

    @post("/batch-delete", response_model=ApiResponse[dict])
    async def batch_delete_rows(
        self,
        row_ids: list[str],
        service: ExampleDataService = Depends(get_example_data_service),
        _: dict = Depends(require_permission("example:delete")),
    ) -> dict:
        """批量删除。"""
        deleted = await service.batch_delete_rows(row_ids)
        return success_response(data={"deleted": deleted}, message=f"已删除 {deleted} 行")

    @post("/batch-save", response_model=ApiResponse[dict])
    async def batch_save(
        self,
        dto: ExampleDataBatchSaveDTO,
        service: ExampleDataService = Depends(get_example_data_service),
        user_id: str = Depends(get_current_user_id),
        _: dict = Depends(require_permission("example:edit")),
    ) -> dict:
        """批量保存（Univer 页面差异回写：creates + updates + deletes 单事务）。

        注意：删除走 example:delete 语义，但表格页统一以 example:edit
        守护（编辑面内的行删除视为编辑的一部分）。
        """
        result = await service.batch_save(dto, operator_id=user_id)
        return success_response(data=result, message="保存成功")
