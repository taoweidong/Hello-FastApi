"""通知公告路由模块。

提供通知公告的增删改查功能。
路由前缀: /api/system/notice
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends

from src.api.common import list_response, success_response
from src.api.common.response_schemas import ApiResponse, PaginatedResponse
from src.api.dependencies import get_current_active_user, get_notice_service, require_permission
from src.application.dto.notice_dto import NoticeCreateDTO, NoticeListQueryDTO, NoticeUpdateDTO
from src.application.dto.user_dto import BatchDeleteDTO
from src.application.services.notice_service import NoticeService
from src.domain.entities.user import UserEntity


class NoticeRouter(Routable):
    """通知公告路由类，提供通知公告增删改查功能。"""

    @post("", response_model=PaginatedResponse[dict])
    async def get_notice_list(
        self,
        query: NoticeListQueryDTO,
        service: NoticeService = Depends(get_notice_service),
        _: dict = Depends(require_permission("notice:view")),
    ) -> dict:
        """获取通知公告列表（分页）。"""
        notices, total = await service.get_notices(query)
        return list_response(
            list_data=[n.model_dump() for n in notices],
            total=total,
            page_size=query.pageSize,
            current_page=query.pageNum,
        )

    @get("/latest", response_model=ApiResponse[list[dict]])
    async def get_latest_notices(
        self, _: UserEntity = Depends(get_current_active_user), service: NoticeService = Depends(get_notice_service)
    ) -> dict:
        """获取最新启用公告（仅需登录，供顶栏通知铃铛展示）。"""
        notices = await service.get_latest_notices()
        return success_response(data=[n.model_dump() for n in notices])

    @post("/create", response_model=ApiResponse[dict])
    async def create_notice(
        self,
        dto: NoticeCreateDTO,
        current_user: UserEntity = Depends(get_current_active_user),
        service: NoticeService = Depends(get_notice_service),
        _: dict = Depends(require_permission("notice:add")),
    ) -> dict:
        """创建通知公告。"""
        notice = await service.create_notice(dto, current_user)
        return success_response(data=notice.model_dump(), message="创建成功", code=201)

    @post("/batch-delete", response_model=ApiResponse[dict])
    async def batch_delete_notices(
        self,
        dto: BatchDeleteDTO,
        service: NoticeService = Depends(get_notice_service),
        _: dict = Depends(require_permission("notice:delete")),
    ) -> dict:
        """批量删除通知公告。"""
        result = await service.batch_delete_notices(dto.ids)
        return success_response(data=result, message="批量删除成功")

    @get("/{notice_id}", response_model=ApiResponse[dict])
    async def get_notice(
        self,
        notice_id: str,
        service: NoticeService = Depends(get_notice_service),
        _: dict = Depends(require_permission("notice:view")),
    ) -> dict:
        """获取通知公告详情。"""
        notice = await service.get_notice(notice_id)
        return success_response(data=notice.model_dump())

    @put("/{notice_id}", response_model=ApiResponse[dict])
    async def update_notice(
        self,
        notice_id: str,
        dto: NoticeUpdateDTO,
        current_user: UserEntity = Depends(get_current_active_user),
        service: NoticeService = Depends(get_notice_service),
        _: dict = Depends(require_permission("notice:edit")),
    ) -> dict:
        """更新通知公告。"""
        notice = await service.update_notice(notice_id, dto, current_user)
        return success_response(data=notice.model_dump(), message="更新成功")

    @delete("/{notice_id}", response_model=ApiResponse[None])
    async def delete_notice(
        self,
        notice_id: str,
        service: NoticeService = Depends(get_notice_service),
        _: dict = Depends(require_permission("notice:delete")),
    ) -> dict:
        """删除通知公告。"""
        await service.delete_notice(notice_id)
        return success_response(message="删除成功")
