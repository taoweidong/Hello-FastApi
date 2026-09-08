"""应用层 - 通知公告服务。"""

from src.application.dto.notice_dto import NoticeCreateDTO, NoticeListQueryDTO, NoticeResponseDTO, NoticeUpdateDTO
from src.domain.entities.notice import NoticeEntity
from src.domain.entities.user import UserEntity
from src.domain.exceptions import NotFoundError
from src.domain.repositories.notice_repository import NoticeRepositoryInterface


class NoticeService:
    """通知公告操作的应用服务。"""

    def __init__(self, notice_repo: NoticeRepositoryInterface):
        self.notice_repo = notice_repo

    async def create_notice(self, dto: NoticeCreateDTO, current_user: UserEntity) -> NoticeResponseDTO:
        """创建通知公告（记录发布人信息）。"""
        notice_entity = NoticeEntity.create_new(
            title=dto.title,
            content=dto.content,
            notice_type=dto.noticeType,
            publisher_id=current_user.id,
            publisher_name=current_user.nickname or current_user.username,
        )
        notice_entity.is_active = dto.isActive
        notice_entity.creator_id = current_user.id
        created = await self.notice_repo.create(notice_entity)
        return self._to_response(created)

    async def get_notice(self, notice_id: str) -> NoticeResponseDTO:
        """根据ID获取公告。"""
        notice = await self.notice_repo.get_by_id(notice_id)
        if notice is None:
            raise NotFoundError(f"公告 ID '{notice_id}' 不存在")
        return self._to_response(notice)

    async def get_notices(self, query: NoticeListQueryDTO) -> tuple[list[NoticeResponseDTO], int]:
        """获取公告列表。"""
        total = await self.notice_repo.count(title=query.title, notice_type=query.noticeType, is_active=query.isActive)
        notices = await self.notice_repo.get_all(
            page_num=query.pageNum,
            page_size=query.pageSize,
            title=query.title,
            notice_type=query.noticeType,
            is_active=query.isActive,
        )
        return [self._to_response(n) for n in notices], total

    async def get_latest_notices(self, limit: int = 5) -> list[NoticeResponseDTO]:
        """获取最新启用的公告（供顶栏通知铃铛展示）。"""
        notices = await self.notice_repo.get_all(page_num=1, page_size=limit, is_active=1)
        return [self._to_response(n) for n in notices]

    async def update_notice(self, notice_id: str, dto: NoticeUpdateDTO, current_user: UserEntity) -> NoticeResponseDTO:
        """更新公告。"""
        notice = await self.notice_repo.get_by_id(notice_id)
        if notice is None:
            raise NotFoundError(f"公告 ID '{notice_id}' 不存在")

        notice.update_info(title=dto.title, content=dto.content, notice_type=dto.noticeType, is_active=dto.isActive)
        notice.modifier_id = current_user.id
        updated = await self.notice_repo.update(notice)
        return self._to_response(updated)

    async def delete_notice(self, notice_id: str) -> bool:
        """删除公告。"""
        if not await self.notice_repo.delete(notice_id):
            raise NotFoundError(f"公告 ID '{notice_id}' 不存在")
        return True

    async def batch_delete_notices(self, notice_ids: list[str]) -> dict:
        """批量删除公告。"""
        deleted_count = await self.notice_repo.batch_delete(notice_ids)
        return {"deleted_count": deleted_count, "total_requested": len(notice_ids)}

    @staticmethod
    def _to_response(notice: NoticeEntity) -> NoticeResponseDTO:
        """将公告实体转换为响应 DTO。"""
        return NoticeResponseDTO(
            id=notice.id,
            title=notice.title,
            content=notice.content,
            noticeType=notice.notice_type,
            isActive=notice.is_active,
            publisherId=notice.publisher_id,
            publisherName=notice.publisher_name,
            creatorId=notice.creator_id,
            modifierId=notice.modifier_id,
            createdTime=notice.created_time,
            updatedTime=notice.updated_time,
        )
