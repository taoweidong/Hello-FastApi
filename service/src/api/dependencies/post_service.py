"""岗位应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.post_service import PostService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.post_repository import PostRepository


async def get_post_service(db: AsyncSession = Depends(get_db)) -> PostService:
    """获取岗位服务实例。"""
    post_repo = PostRepository(db)
    return PostService(post_repo=post_repo)
