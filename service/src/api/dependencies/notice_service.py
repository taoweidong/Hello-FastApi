"""通知公告应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.notice_service import NoticeService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.notice_repository import NoticeRepository


async def get_notice_service(db: AsyncSession = Depends(get_db)) -> NoticeService:
    """获取通知公告服务实例。"""
    notice_repo = NoticeRepository(db)
    return NoticeService(notice_repo=notice_repo)
